#!/usr/bin/env python3
"""Create a reproducible quality report for the BEST-only baseline outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence

from build_best_baseline import parse_gtfs_time

BKC_REFERENCE_URL = "https://www.bestundertaking.com/assets/pdf/mmrconnect.pdf"
OFFICIAL_BKC_LABELS = (
    "BKC-10",
    "BKC-11",
    "BKC-12",
    "BKC-13",
    "BKC-21",
    "BKC-22",
    "BKC-23",
    "BKC-24",
    "BKC-25",
)
SECONDS_PER_DAY = 24 * 60 * 60


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise ValueError(f"Missing required baseline output: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames or []
        if not headers or len(headers) != len(set(headers)):
            raise ValueError(f"Invalid header in {path.name}")
        rows = []
        for row in reader:
            if None in row:
                raise ValueError(f"Malformed row in {path.name}")
            rows.append(
                {str(key): value.strip() if value is not None else "" for key, value in row.items()}
            )
    return headers, rows


def read_header(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Missing required baseline output: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        headers = next(csv.reader(source), [])
    if not headers or len(headers) != len(set(headers)):
        raise ValueError(f"Invalid header in {path.name}")
    return headers


def classify_duration(
    start_seconds: int | None,
    end_seconds: int | None,
    distinct_times: set[int],
) -> str:
    if start_seconds is None or end_seconds is None:
        return "duration_unavailable"
    if end_seconds < start_seconds:
        return "negative_duration"
    if end_seconds > start_seconds:
        return "positive_duration"
    if len(distinct_times) <= 1:
        return "zero_duration_one_distinct_time"
    return "zero_duration_endpoint_variation"


def write_csv(
    path: Path, headers: Sequence[str], rows: Iterable[dict[str, object]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target, fieldnames=headers, extrasaction="raise", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def summarize_duration(values: Sequence[int]) -> dict[str, int | float | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(sum(values) / len(values), 2),
        "max": max(values),
    }


def qualify_baseline(
    raw_dir: Path, baseline_dir: Path, output_dir: Path
) -> dict[str, object]:
    raw_dir = raw_dir.resolve()
    baseline_dir = baseline_dir.resolve()
    output_dir = output_dir.resolve()
    if raw_dir == output_dir or raw_dir in output_dir.parents:
        raise ValueError("Qualification outputs must be outside raw input data")

    baseline_metrics_path = baseline_dir / "baseline_metrics.json"
    if not baseline_metrics_path.is_file():
        raise ValueError(f"Run the BEST baseline builder first: {baseline_metrics_path}")
    baseline = json.loads(baseline_metrics_path.read_text(encoding="utf-8"))
    expected_hashes = baseline["source"]["sha256"]
    actual_hashes = {
        name: sha256_file(raw_dir / name) for name in sorted(expected_hashes)
    }
    if actual_hashes != expected_hashes:
        raise ValueError(
            "Raw inputs differ from the baseline snapshot; rebuild the BEST baseline first"
        )

    _, route_rows = read_rows(baseline_dir / "best_routes.csv")
    _, trip_rows = read_rows(baseline_dir / "best_trips.csv")
    _, pattern_rows = read_rows(baseline_dir / "route_patterns.csv")
    stop_time_headers = read_header(baseline_dir / "best_stop_times.csv")

    routes = {row["route_id"]: row for row in route_rows}
    trips = {row["trip_id"]: row for row in trip_rows}
    if len(routes) != len(route_rows) or len(trips) != len(trip_rows):
        raise ValueError("Duplicate route_id or trip_id in BEST baseline outputs")

    pattern_by_path: dict[tuple[str, str, tuple[str, ...]], dict[str, str]] = {}
    for row in pattern_rows:
        key = (
            row["route_id"],
            row.get("direction_id", ""),
            tuple(json.loads(row["stop_ids_json"])),
        )
        if key in pattern_by_path:
            raise ValueError(f"Duplicate route pattern key: {row['pattern_id']}")
        pattern_by_path[key] = row

    pattern_stats: dict[str, dict[str, object]] = {}
    for row in pattern_rows:
        pattern_stats[row["pattern_id"]] = {
            "pattern_id": row["pattern_id"],
            "route_id": row["route_id"],
            "route_short_name": row.get("route_short_name", ""),
            "route_long_name": row.get("route_long_name", ""),
            "direction_id": row.get("direction_id", ""),
            "stop_count": int(row["stop_count"]),
            "trip_count": 0,
            "stop_time_rows": 0,
            "positive_duration_count": 0,
            "zero_duration_count": 0,
            "zero_duration_one_distinct_time_count": 0,
            "zero_duration_endpoint_variation_count": 0,
            "duration_unavailable_count": 0,
            "post_midnight_trip_count": 0,
            "_durations": [],
        }
    route_stats: dict[str, dict[str, object]] = {}
    for route_id, route in routes.items():
        route_stats[route_id] = {
            "route_id": route_id,
            "route_short_name": route.get("route_short_name", ""),
            "route_long_name": route.get("route_long_name", ""),
            "trip_count": 0,
            "stop_time_rows": 0,
            "pattern_count": 0,
            "positive_duration_count": 0,
            "zero_duration_count": 0,
            "zero_duration_one_distinct_time_count": 0,
            "zero_duration_endpoint_variation_count": 0,
            "duration_unavailable_count": 0,
            "post_midnight_trip_count": 0,
            "_durations": [],
            "_patterns": set(),
        }

    zero_duration_rows: list[dict[str, object]] = []
    post_midnight_rows: list[dict[str, object]] = []
    durations: list[int] = []
    category_counts: Counter[str] = Counter()

    total_time_fields = 0
    total_missing_time_fields = 0
    total_after_midnight_fields = 0
    total_after_midnight_rows = 0
    max_service_hour: int | None = None
    trips_with_post_midnight_time = 0
    all_trip_ids_seen: set[str] = set()
    current_trip_id: str | None = None
    current: dict[str, object] | None = None
    previous_sequence: int | None = None

    def begin_trip(trip_id: str) -> dict[str, object]:
        if trip_id not in trips:
            raise ValueError(f"Stop-time output references unknown trip_id {trip_id}")
        return {
            "trip_id": trip_id,
            "route_id": trips[trip_id]["route_id"],
            "direction_id": trips[trip_id].get("direction_id", ""),
            "stop_ids": [],
            "rows": 0,
            "first_seconds": None,
            "first_time": "",
            "last_seconds": None,
            "last_time": "",
            "distinct_times": set(),
            "arrival_blank": 0,
            "departure_blank": 0,
            "timepoint_count": 0,
            "time_fields": 0,
            "after_midnight_fields": 0,
            "after_midnight_rows": 0,
            "maximum_hour": None,
            "timepoint_values": set(),
        }

    def finish_trip(state: dict[str, object]) -> None:
        nonlocal total_time_fields, total_missing_time_fields
        nonlocal total_after_midnight_fields, total_after_midnight_rows
        nonlocal max_service_hour, trips_with_post_midnight_time
        trip_id = str(state["trip_id"])
        route_id = str(state["route_id"])
        route = routes[route_id]
        stop_ids = tuple(state["stop_ids"])
        direction_id = str(state["direction_id"])
        pattern_key = (route_id, direction_id, stop_ids)
        pattern = pattern_by_path.get(pattern_key)
        if pattern is None:
            raise ValueError(f"No route pattern found for trip {trip_id}")
        pattern_id = pattern["pattern_id"]
        start_seconds = state["first_seconds"]
        end_seconds = state["last_seconds"]
        distinct_times = state["distinct_times"]
        duration_class = classify_duration(
            start_seconds if isinstance(start_seconds, int) else None,
            end_seconds if isinstance(end_seconds, int) else None,
            distinct_times if isinstance(distinct_times, set) else set(),
        )
        duration_seconds = (
            end_seconds - start_seconds
            if isinstance(start_seconds, int) and isinstance(end_seconds, int)
            else None
        )
        if duration_seconds is not None and duration_seconds < 0:
            raise ValueError(f"Negative scheduled duration for trip {trip_id}")

        state["pattern_id"] = pattern_id
        state["duration_seconds"] = duration_seconds
        state["duration_class"] = duration_class
        category_counts[duration_class] += 1
        all_trip_ids_seen.add(trip_id)

        route_stat = route_stats[route_id]
        pattern_stat = pattern_stats[pattern_id]
        for stats in (route_stat, pattern_stat):
            stats["trip_count"] = int(stats["trip_count"]) + 1
            stats["stop_time_rows"] = int(stats["stop_time_rows"]) + int(state["rows"])
            if duration_class == "positive_duration":
                stats["positive_duration_count"] = int(stats["positive_duration_count"]) + 1
            elif duration_class.startswith("zero_duration"):
                stats["zero_duration_count"] = int(stats["zero_duration_count"]) + 1
                category_field = f"{duration_class}_count"
                stats[category_field] = int(stats[category_field]) + 1
            elif duration_class == "duration_unavailable":
                stats["duration_unavailable_count"] = int(stats["duration_unavailable_count"]) + 1
            if duration_seconds is not None:
                stats["_durations"].append(duration_seconds)

        route_stat["_patterns"].add(pattern_id)
        is_post_midnight = int(state["after_midnight_fields"]) > 0
        if is_post_midnight:
            trips_with_post_midnight_time += 1
            route_stat["post_midnight_trip_count"] = int(
                route_stat["post_midnight_trip_count"]
            ) + 1
            pattern_stat["post_midnight_trip_count"] = int(
                pattern_stat["post_midnight_trip_count"]
            ) + 1
            post_midnight_rows.append(
                {
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "route_short_name": route.get("route_short_name", ""),
                    "direction_id": direction_id,
                    "pattern_id": pattern_id,
                    "stop_count": len(stop_ids),
                    "start_time": state["first_time"],
                    "end_time": state["last_time"],
                    "maximum_gtfs_hour": state["maximum_hour"],
                    "time_fields_at_or_after_24h": state["after_midnight_fields"],
                    "stop_time_rows_at_or_after_24h": state["after_midnight_rows"],
                    "timepoint_stops": state["timepoint_count"],
                }
            )

        if duration_seconds is not None:
            durations.append(duration_seconds)
        if duration_class.startswith("zero_duration"):
            zero_duration_rows.append(
                {
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "route_short_name": route.get("route_short_name", ""),
                    "route_long_name": route.get("route_long_name", ""),
                    "direction_id": direction_id,
                    "pattern_id": pattern_id,
                    "stop_count": len(stop_ids),
                    "stop_time_rows": state["rows"],
                    "start_time": state["first_time"],
                    "end_time": state["last_time"],
                    "duration_seconds": duration_seconds,
                    "classification": duration_class,
                    "distinct_time_values": len(distinct_times),
                    "time_fields": state["time_fields"],
                    "missing_arrival_fields": state["arrival_blank"],
                    "missing_departure_fields": state["departure_blank"],
                    "timepoint_stops": state["timepoint_count"],
                    "post_midnight_time_fields": state["after_midnight_fields"],
                }
            )

        total_time_fields += int(state["time_fields"])
        total_missing_time_fields += int(state["arrival_blank"]) + int(
            state["departure_blank"]
        )
        total_after_midnight_fields += int(state["after_midnight_fields"])
        total_after_midnight_rows += int(state["after_midnight_rows"])
        trip_max_hour = state["maximum_hour"]
        if isinstance(trip_max_hour, int):
            max_service_hour = (
                trip_max_hour
                if max_service_hour is None
                else max(max_service_hour, trip_max_hour)
            )

    stop_time_path = baseline_dir / "best_stop_times.csv"
    with stop_time_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != stop_time_headers:
            raise ValueError("best_stop_times.csv header changed during processing")
        for raw_row in reader:
            if None in raw_row:
                raise ValueError("Malformed row in best_stop_times.csv")
            row = {
                str(key): value.strip() if value is not None else ""
                for key, value in raw_row.items()
            }
            trip_id = row["trip_id"]
            stop_sequence = int(row["stop_sequence"])
            if trip_id != current_trip_id:
                if current is not None:
                    finish_trip(current)
                current_trip_id = trip_id
                current = begin_trip(trip_id)
                previous_sequence = None
            if previous_sequence is not None and stop_sequence <= previous_sequence:
                raise ValueError(f"Stop sequence is not strictly increasing for {trip_id}")
            previous_sequence = stop_sequence
            assert current is not None
            current["rows"] = int(current["rows"]) + 1
            current["stop_ids"].append(row["stop_id"])

            arrival_seconds = parse_gtfs_time(row.get("arrival_time"))
            departure_seconds = parse_gtfs_time(row.get("departure_time"))
            row_has_after_midnight_time = False
            for field_name, seconds in (
                ("arrival_time", arrival_seconds),
                ("departure_time", departure_seconds),
            ):
                if seconds is None:
                    current["arrival_blank" if field_name == "arrival_time" else "departure_blank"] = (
                        int(current["arrival_blank" if field_name == "arrival_time" else "departure_blank"])
                        + 1
                    )
                    continue
                current["time_fields"] = int(current["time_fields"]) + 1
                current["distinct_times"].add(seconds)

                hour = seconds // 3600
                current["maximum_hour"] = (
                    hour
                    if current["maximum_hour"] is None
                    else max(int(current["maximum_hour"]), hour)
                )
                if seconds >= SECONDS_PER_DAY:
                    current["after_midnight_fields"] = int(
                        current["after_midnight_fields"]
                    ) + 1
                    row_has_after_midnight_time = True
            if row_has_after_midnight_time:
                current["after_midnight_rows"] = int(current["after_midnight_rows"]) + 1
            if row.get("timepoint", "") == "1":
                current["timepoint_values"].add(stop_sequence)
            for value in (arrival_seconds, departure_seconds):
                if value is not None and current["first_seconds"] is None:
                    current["first_seconds"] = (
                        departure_seconds
                        if departure_seconds is not None
                        else arrival_seconds
                    )
                    current["first_time"] = (
                        row["departure_time"]
                        if departure_seconds is not None
                        else row["arrival_time"]
                    )
                if value is not None:
                    current["last_seconds"] = (
                        arrival_seconds
                        if arrival_seconds is not None
                        else departure_seconds
                    )
                    current["last_time"] = (
                        row["arrival_time"]
                        if arrival_seconds is not None
                        else row["departure_time"]
                    )
            current["timepoint_count"] = len(current["timepoint_values"])
    if current is not None:
        finish_trip(current)

    for stats in route_stats.values():
        stats["pattern_count"] = len(stats["_patterns"])
        del stats["_patterns"]
        stats["zero_duration_rate"] = ratio(
            int(stats["zero_duration_count"]), int(stats["trip_count"])
        )
        stats["mean_duration_seconds"] = (
            round(sum(stats["_durations"]) / len(stats["_durations"]), 2)
            if stats["_durations"]
            else None
        )
        stats["median_duration_seconds"] = (
            statistics.median(stats["_durations"]) if stats["_durations"] else None
        )
        del stats["_durations"]
    for stats in pattern_stats.values():
        stats["zero_duration_rate"] = ratio(
            int(stats["zero_duration_count"]), int(stats["trip_count"])
        )
        stats["mean_duration_seconds"] = (
            round(sum(stats["_durations"]) / len(stats["_durations"]), 2)
            if stats["_durations"]
            else None
        )
        stats["median_duration_seconds"] = (
            statistics.median(stats["_durations"]) if stats["_durations"] else None
        )
        del stats["_durations"]

    expected_trips = int(baseline["scope"]["best_counts"]["trips"])
    expected_zero = int(
        baseline["trip_duration_seconds"]["zero_duration_trip_count"]
    )
    expected_post_midnight = int(
        baseline["service_time"]["trips_with_any_time_at_or_after_24h"]
    )
    if len(all_trip_ids_seen) != expected_trips:
        raise ValueError(
            f"Processed {len(all_trip_ids_seen)} trips, expected {expected_trips}"
        )
    if len(zero_duration_rows) != expected_zero:
        raise ValueError(
            f"Found {len(zero_duration_rows)} zero-duration trips, expected {expected_zero}"
        )
    if trips_with_post_midnight_time != expected_post_midnight:
        raise ValueError(
            f"Found {trips_with_post_midnight_time} post-midnight trips, "
            f"expected {expected_post_midnight}"
        )
    if total_after_midnight_rows != int(
        baseline["service_time"]["stop_time_rows_with_any_time_at_or_after_24h"]
    ):
        raise ValueError("Post-midnight stop-time row count disagrees with baseline")

    official_label_matches = sorted(
        set(OFFICIAL_BKC_LABELS)
        & {row.get("route_short_name", "") for row in route_rows}
    )
    summary: dict[str, object] = {
        "report": {
            "name": "BEST baseline quality qualification",
            "version": "1.0.0",
            "basis": "Re-audit of deterministic BEST baseline outputs against the same hashed raw snapshot.",
            "time_rule": "GTFS times are elapsed service-day seconds; hours at or above 24 are not wrapped.",
        },
        "source": {
            "feed_publisher_name": baseline["source"]["feed_publisher_name"],
            "declared_feed_start_date": baseline["source"]["declared_feed_start_date"],
            "declared_feed_end_date": baseline["source"]["declared_feed_end_date"],
            "raw_sha256": actual_hashes,
        },
        "scope": {
            "routes": len(routes),
            "trips": len(trips),
            "patterns": len(pattern_rows),
            "stop_time_rows": sum(int(row["stop_time_rows"]) for row in pattern_stats.values()),
        },
        "duration_quality": {
            "trip_duration_seconds": summarize_duration(durations),
            "trips_by_classification": dict(sorted(category_counts.items())),
            "zero_duration_trip_count": len(zero_duration_rows),
            "zero_duration_trip_share": ratio(len(zero_duration_rows), len(trips)),
            "zero_duration_by_pattern_classification": {
                key: sum(1 for row in zero_duration_rows if row["classification"] == key)
                for key in (
                    "zero_duration_one_distinct_time",
                    "zero_duration_endpoint_variation",
                )
            },
            "time_fields_present": total_time_fields,
            "time_fields_missing": total_missing_time_fields,
            "time_fields_expected": sum(int(row["stop_time_rows"]) for row in pattern_stats.values()) * 2,
        },
        "post_midnight_quality": {
            "trips_with_any_time_at_or_after_24h": trips_with_post_midnight_time,
            "time_fields_at_or_after_24h": total_after_midnight_fields,
            "stop_time_rows_with_any_time_at_or_after_24h": total_after_midnight_rows,
            "maximum_gtfs_hour": max_service_hour,
        },
        "cross_check": {
            "reference_title": "Bandra Kurla Complex Routes (Air Conditioned)",
            "reference_url": BKC_REFERENCE_URL,
            "official_route_labels_checked": list(OFFICIAL_BKC_LABELS),
            "match_method": "Exact comparison with BEST routes.route_short_name.",
            "exact_route_label_matches": official_label_matches,
            "effective_date": "Not identified in the PDF text reviewed.",
            "result": (
                "No direct route-label match; this reference cannot validate the supplied feed's schedules."
                if not official_label_matches
                else "Route-label matches found; schedule comparison still requires an effective-date match."
            ),
        },
        "validation": {
            "all_best_trips_accounted_for": len(all_trip_ids_seen) == expected_trips,
            "zero_duration_count_matches_baseline": len(zero_duration_rows) == expected_zero,
            "post_midnight_count_matches_baseline": (
                trips_with_post_midnight_time == expected_post_midnight
            ),
            "raw_hashes_match_baseline": actual_hashes == expected_hashes,
        },
        "interpretation": [
            "Zero schedule duration is a data-quality flag, not a zero travel-time claim.",
            "The official BKC PDF provides a narrow route/time/itinerary reference, but its labels do not match BEST route_short_name values in this feed.",
            "No license, official GTFS provenance, or feed completeness is established by this cross-check.",
        ],
    }

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".best-qualification-", dir=output_dir.parent
    ) as staging_name:
        staging = Path(staging_name)
        zero_duration_rows.sort(key=lambda row: str(row["trip_id"]))
        post_midnight_rows.sort(key=lambda row: str(row["trip_id"]))
        write_csv(
            staging / "zero_duration_trips.csv",
            (
                "trip_id",
                "route_id",
                "route_short_name",
                "route_long_name",
                "direction_id",
                "pattern_id",
                "stop_count",
                "stop_time_rows",
                "start_time",
                "end_time",
                "duration_seconds",
                "classification",
                "distinct_time_values",
                "time_fields",
                "missing_arrival_fields",
                "missing_departure_fields",
                "timepoint_stops",
                "post_midnight_time_fields",
            ),
            zero_duration_rows,
        )
        write_csv(
            staging / "post_midnight_trips.csv",
            (
                "trip_id",
                "route_id",
                "route_short_name",
                "direction_id",
                "pattern_id",
                "stop_count",
                "start_time",
                "end_time",
                "maximum_gtfs_hour",
                "time_fields_at_or_after_24h",
                "stop_time_rows_at_or_after_24h",
                "timepoint_stops",
            ),
            post_midnight_rows,
        )
        pattern_output = []
        for row in pattern_stats.values():
            pattern_output.append(
                {key: value for key, value in row.items() if not key.startswith("_")}
            )
        pattern_output.sort(
            key=lambda row: (
                str(row["route_id"]),
                str(row["direction_id"]),
                str(row["pattern_id"]),
            )
        )
        pattern_headers = (
            "pattern_id",
            "route_id",
            "route_short_name",
            "route_long_name",
            "direction_id",
            "stop_count",
            "trip_count",
            "stop_time_rows",
            "positive_duration_count",
            "zero_duration_count",
            "zero_duration_one_distinct_time_count",
            "zero_duration_endpoint_variation_count",
            "duration_unavailable_count",
            "post_midnight_trip_count",
            "zero_duration_rate",
            "mean_duration_seconds",
            "median_duration_seconds",
        )
        write_csv(staging / "route_pattern_quality.csv", pattern_headers, pattern_output)

        route_output = []
        for row in route_stats.values():
            route_output.append(
                {key: value for key, value in row.items() if not key.startswith("_")}
            )
        route_output.sort(key=lambda row: str(row["route_id"]))
        route_headers = (
            "route_id",
            "route_short_name",
            "route_long_name",
            "trip_count",
            "pattern_count",
            "stop_time_rows",
            "positive_duration_count",
            "zero_duration_count",
            "zero_duration_one_distinct_time_count",
            "zero_duration_endpoint_variation_count",
            "duration_unavailable_count",
            "post_midnight_trip_count",
            "zero_duration_rate",
            "mean_duration_seconds",
            "median_duration_seconds",
        )
        write_csv(staging / "route_quality.csv", route_headers, route_output)
        (staging / "baseline_quality_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        for staged_file in sorted(staging.iterdir()):
            if staged_file.is_file():
                os.replace(staged_file, output_dir / staged_file.name)
    return summary


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Qualify the BEST-only baseline's zero-duration and post-midnight trips."
    )
    parser.add_argument("--input", type=Path, default=project_root / "data" / "raw")
    parser.add_argument(
        "--baseline", type=Path, default=project_root / "data" / "processed" / "best"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "data" / "processed" / "best" / "qualification",
    )
    args = parser.parse_args()
    try:
        summary = qualify_baseline(args.input, args.baseline, args.output)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
