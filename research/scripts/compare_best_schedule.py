#!/usr/bin/env python3
"""Compare one dated BEST first-stop schedule extract with a processed GTFS baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

TIME_RE = re.compile(r"^([0-9]+):([0-5][0-9]):([0-5][0-9])$")
WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def parse_gtfs_time(value: str | None) -> int | None:
    """Return elapsed service-day seconds; values after 24:00 remain unwrapped."""
    if value is None or value.strip() == "":
        return None
    match = TIME_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid GTFS time {value!r}; expected HH:MM:SS")
    hours, minutes, seconds = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def format_gtfs_time(seconds: int) -> str:
    if seconds < 0:
        raise ValueError("GTFS time seconds cannot be negative")
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Required file is missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"{path.name} has no header row")
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {missing}")
        return [dict(row) for row in reader]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Required file is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_raw_snapshot(
    baseline_metrics: dict[str, Any], raw_dir: Path | None
) -> dict[str, Any]:
    source = baseline_metrics.get("source", {})
    expected = source.get("sha256", {}) if isinstance(source, dict) else {}
    if not raw_dir or not expected:
        return {"status": "unavailable", "checked_files": 0, "mismatches": []}

    missing = [name for name in sorted(expected) if not (raw_dir / name).is_file()]
    if missing:
        return {
            "status": "unavailable",
            "checked_files": 0,
            "missing_files": missing,
            "mismatches": [],
        }

    mismatches = [
        name for name, digest in sorted(expected.items())
        if sha256_file(raw_dir / name) != digest
    ]
    return {
        "status": "verified" if not mismatches else "mismatch",
        "checked_files": len(expected),
        "mismatches": mismatches,
    }


def active_service_ids(
    calendar_rows: list[dict[str, str]], service_date: date
) -> set[str]:
    day_column = WEEKDAYS[service_date.weekday()]
    active: set[str] = set()
    target = service_date.strftime("%Y%m%d")
    for row in calendar_rows:
        if row["start_date"] <= target <= row["end_date"] and row[day_column] == "1":
            active.add(row["service_id"])
    return active


def load_reference_times(path: Path) -> Counter[int]:
    rows = read_csv(path, {"departure_time"})
    if not rows:
        raise ValueError("Reference departure file contains no times")
    times: Counter[int] = Counter()
    for row_number, row in enumerate(rows, start=2):
        seconds = parse_gtfs_time(row["departure_time"])
        if seconds is None:
            raise ValueError(f"Blank reference departure at CSV row {row_number}")
        times[seconds] += 1
    return times


def compare_schedule_reference(
    baseline_dir: Path,
    reference_csv: Path,
    metadata_path: Path,
    output_dir: Path,
    raw_dir: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    baseline_dir = baseline_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}; pass overwrite=True "
            "only to replace generated comparison files"
        )

    metadata = read_json(metadata_path)
    required_metadata = (
        "reference_id",
        "source_name",
        "source_url",
        "source_data_retrieved_from_chalo",
        "observed_on",
        "reference_route_label",
        "reference_origin_stop",
        "reference_service_days",
        "service_date_compared",
        "gtfs_route_id",
        "gtfs_route_short_name",
        "gtfs_direction_id",
        "gtfs_origin_stop_id",
    )
    missing_metadata = [key for key in required_metadata if key not in metadata]
    if missing_metadata:
        raise ValueError(f"Reference metadata is missing: {missing_metadata}")

    try:
        service_date = date.fromisoformat(metadata["service_date_compared"])
    except (TypeError, ValueError) as error:
        raise ValueError("service_date_compared must be an ISO date") from error
    weekday_name = service_date.strftime("%A")
    if weekday_name not in metadata["reference_service_days"]:
        raise ValueError(
            f"Comparison date is {weekday_name}, outside the reference service days"
        )

    baseline_metrics = read_json(baseline_dir / "baseline_metrics.json")
    raw_snapshot = verify_raw_snapshot(baseline_metrics, raw_dir)

    routes = read_csv(
        baseline_dir / "best_routes.csv",
        {"route_id", "agency_id", "route_short_name", "route_long_name"},
    )
    route_id = metadata["gtfs_route_id"]
    route_rows = [row for row in routes if row["route_id"] == route_id]
    if len(route_rows) != 1:
        raise ValueError(f"Expected one baseline route {route_id}; found {len(route_rows)}")
    route = route_rows[0]
    if route["agency_id"] != "BEST":
        raise ValueError(f"Route {route_id} is not tagged to BEST")
    if route["route_short_name"] != metadata["gtfs_route_short_name"]:
        raise ValueError(
            f"GTFS route label changed: expected {metadata['gtfs_route_short_name']!r}, "
            f"found {route['route_short_name']!r}"
        )

    calendars = read_csv(
        baseline_dir / "best_calendar.csv",
        {"service_id", *WEEKDAYS, "start_date", "end_date"},
    )
    services = active_service_ids(calendars, service_date)
    trips = read_csv(
        baseline_dir / "best_trips.csv",
        {"route_id", "service_id", "trip_id", "direction_id"},
    )
    route_trips = {
        row["trip_id"]
        for row in trips
        if row["route_id"] == route_id
        and row["direction_id"] == metadata["gtfs_direction_id"]
        and row["service_id"] in services
    }
    if not route_trips:
        raise ValueError(
            f"No active trips for route {route_id} on {service_date.isoformat()}"
        )

    first_events: dict[str, tuple[int, str, int | None]] = {}
    stop_time_path = baseline_dir / "best_stop_times.csv"
    if not stop_time_path.is_file():
        raise ValueError(f"Required file is missing: {stop_time_path}")
    with stop_time_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required_stop_time_columns = {
            "trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"
        }
        missing = sorted(required_stop_time_columns - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"best_stop_times.csv is missing columns: {missing}")
        for row in reader:
            trip_id = row["trip_id"]
            if trip_id not in route_trips:
                continue
            try:
                sequence = int(row["stop_sequence"])
            except ValueError as error:
                raise ValueError(
                    f"Invalid stop_sequence for trip {trip_id}: {row['stop_sequence']!r}"
                ) from error
            event_time = row["departure_time"] or row["arrival_time"]
            event_seconds = parse_gtfs_time(event_time)
            candidate = (sequence, row["stop_id"], event_seconds)
            previous = first_events.get(trip_id)
            if previous is None or sequence < previous[0]:
                first_events[trip_id] = candidate
            elif sequence == previous[0]:
                raise ValueError(
                    f"Trip {trip_id} contains duplicate first stop_sequence {sequence}"
                )

    if set(first_events) != route_trips:
        missing = sorted(route_trips - set(first_events))
        raise ValueError(f"Trips have no stop-time rows: {missing[:10]}")

    origin_stop_id = metadata["gtfs_origin_stop_id"]
    off_origin_trip_ids = sorted(
        trip_id
        for trip_id, (_, stop_id, _) in first_events.items()
        if stop_id != origin_stop_id
    )
    if off_origin_trip_ids:
        raise ValueError(
            f"Some route trips do not start at the declared origin stop: "
            f"{off_origin_trip_ids[:10]}"
        )

    feed_times: Counter[int] = Counter()
    blank_time_trip_ids: list[str] = []
    for trip_id, (_, _, seconds) in first_events.items():
        if seconds is None:
            blank_time_trip_ids.append(trip_id)
        else:
            feed_times[seconds] += 1
    if blank_time_trip_ids:
        raise ValueError(
            f"First stop times are blank for trips: {sorted(blank_time_trip_ids)[:10]}"
        )

    reference_times = load_reference_times(reference_csv)
    all_times = sorted(set(reference_times) | set(feed_times))
    rows: list[dict[str, Any]] = []
    for seconds in all_times:
        reference_count = reference_times[seconds]
        feed_count = feed_times[seconds]
        if reference_count == 0:
            status = "gtfs_only"
        elif feed_count == 0:
            status = "reference_only"
        elif reference_count == feed_count:
            status = "matched"
        else:
            status = "count_mismatch"
        rows.append(
            {
                "departure_time": format_gtfs_time(seconds),
                "reference_count": reference_count,
                "gtfs_count": feed_count,
                "status": status,
            }
        )

    matched_count = sum(
        min(reference_times[value], feed_times[value])
        for value in set(reference_times) & set(feed_times)
    )
    reference_only_count = sum(
        max(0, count - feed_times[value])
        for value, count in reference_times.items()
    )
    gtfs_only_count = sum(
        max(0, count - reference_times[value])
        for value, count in feed_times.items()
    )
    exact = reference_times == feed_times
    if exact:
        status = "exact"
    elif matched_count:
        status = "partial"
    else:
        status = "no_overlap"

    summary: dict[str, Any] = {
        "schema_version": 1,
        "reference": metadata,
        "gtfs_candidate": {
            "route_id": route_id,
            "route_short_name": route["route_short_name"],
            "route_long_name": route["route_long_name"],
            "direction_id": metadata["gtfs_direction_id"],
            "origin_stop_id": origin_stop_id,
            "service_date": service_date.isoformat(),
            "weekday": weekday_name,
            "active_trip_count": len(route_trips),
            "first_stop_departure_count": sum(feed_times.values()),
            "calendar_exceptions_checked": False,
            "raw_snapshot_check": raw_snapshot,
            "source": baseline_metrics.get("source", {}),
        },
        "comparison": {
            "status": status,
            "matched_departure_count": matched_count,
            "reference_departure_count": sum(reference_times.values()),
            "gtfs_departure_count": sum(feed_times.values()),
            "reference_only_departure_count": reference_only_count,
            "gtfs_only_departure_count": gtfs_only_count,
            "reference_match_share": round(
                matched_count / sum(reference_times.values()), 4
            ),
            "gtfs_match_share": round(
                matched_count / sum(feed_times.values()), 4
            ),
            "reference_only_times": [
                format_gtfs_time(value)
                for value in sorted(reference_times)
                if reference_times[value] > feed_times[value]
            ],
            "gtfs_only_times": [
                format_gtfs_time(value)
                for value in sorted(feed_times)
                if feed_times[value] > reference_times[value]
            ],
        },
        "interpretation": (
            "A time overlap is a descriptive cross-source check, not proof of "
            "operator approval, feed completeness, or schedule accuracy."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "departure_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as target:
        writer = csv.DictWriter(
            target,
            fieldnames=("departure_time", "reference_count", "gtfs_count", "status"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "comparison.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Compare a dated first-stop reference schedule with BEST GTFS."
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=project_root / "data" / "processed" / "best",
    )
    parser.add_argument(
        "--reference-csv",
        type=Path,
        default=project_root / "data" / "references" / "best_321_mon_sat.csv",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=project_root / "data" / "references" / "best_321_mon_sat.json",
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=project_root / "data" / "raw"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to baseline-dir/qualification/schedule_comparisons/<reference_id>.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace comparison outputs already in the selected output directory.",
    )
    args = parser.parse_args()
    try:
        metadata = read_json(args.metadata)
        output_dir = args.output_dir or (
            args.baseline_dir
            / "qualification"
            / "schedule_comparisons"
            / str(metadata["reference_id"])
        )
        summary = compare_schedule_reference(
            args.baseline_dir,
            args.reference_csv,
            args.metadata,
            output_dir,
            raw_dir=args.raw_dir,
            overwrite=args.overwrite,
        )
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(summary["comparison"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

