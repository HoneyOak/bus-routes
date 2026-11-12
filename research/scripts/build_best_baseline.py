#!/usr/bin/env python3
"""Build a deterministic BEST-only GTFS baseline from immutable raw inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import statistics
import tempfile
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

SOURCE_FILES = (
    "agency.txt",
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
    "calendar.txt",
    "feed_info.txt",
)
REQUIRED_COLUMNS = {
    "agency.txt": {"agency_id", "agency_name", "agency_url", "agency_timezone"},
    "routes.txt": {"route_id", "agency_id", "route_type"},
    "trips.txt": {"route_id", "service_id", "trip_id"},
    "stops.txt": {"stop_id", "stop_name", "stop_lat", "stop_lon"},
    "stop_times.txt": {
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    },
    "calendar.txt": {
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    },
    "feed_info.txt": {
        "feed_publisher_name",
        "feed_publisher_url",
        "feed_lang",
        "feed_start_date",
        "feed_end_date",
    },
}
TIME_RE = re.compile(r"^([0-9]+):([0-5][0-9]):([0-5][0-9])$")
SECONDS_PER_DAY = 24 * 60 * 60


def parse_gtfs_time(value: str | None) -> int | None:
    """Parse GTFS HH:MM:SS into seconds; GTFS hours may exceed 24."""
    if value is None or value.strip() == "":
        return None
    text = value.strip()
    match = TIME_RE.fullmatch(text)
    if match is None:
        raise ValueError(f"Invalid GTFS time {value!r}; expected HH:MM:SS")
    hours, minutes, seconds = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def clean_row(row: dict[str | None, str | None]) -> dict[str, str]:
    if None in row:
        raise ValueError("A CSV row contains more values than its header")
    return {
        str(key): (value.strip() if value is not None else "")
        for key, value in row.items()
    }


def read_table(path: Path, required: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise ValueError(f"Missing required GTFS file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames or []
        if not headers:
            raise ValueError(f"{path.name} has no header row")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path.name} has duplicate column names")
        missing = sorted(required - set(headers))
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {missing}")
        rows = [clean_row(row) for row in reader]
    return headers, rows


def unique_index(
    rows: Sequence[dict[str, str]], key: str, filename: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value:
            raise ValueError(f"{filename} contains a blank {key}")
        if value in result:
            raise ValueError(f"{filename} contains duplicate {key}: {value}")
        result[value] = row
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target, fieldnames=headers, extrasaction="raise", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def chronology_issues(
    records: Iterable[tuple[int | None, int | None]],
) -> dict[str, int]:
    """Count within-stop and between-stop schedule decreases for one trip."""
    within_stop = 0
    between_stops = 0
    previous_event_end: int | None = None
    for arrival, departure in records:
        if arrival is not None and departure is not None and arrival > departure:
            within_stop += 1
        event_start = arrival if arrival is not None else departure
        event_end = departure if departure is not None else arrival
        if (
            previous_event_end is not None
            and event_start is not None
            and event_start < previous_event_end
        ):
            between_stops += 1
        if event_end is not None:
            previous_event_end = event_end
    return {
        "arrival_after_departure_rows": within_stop,
        "between_stop_time_decreases": between_stops,
    }


def summarize(values: Sequence[int]) -> dict[str, int | float | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(sum(values) / len(values), 2),
        "max": max(values),
    }


def _read_stop_time_header(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Missing required GTFS file: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames or []
    if not headers:
        raise ValueError("stop_times.txt has no header row")
    if len(headers) != len(set(headers)):
        raise ValueError("stop_times.txt has duplicate column names")
    missing = sorted(REQUIRED_COLUMNS["stop_times.txt"] - set(headers))
    if missing:
        raise ValueError(f"stop_times.txt is missing required columns: {missing}")
    return headers


def build_baseline(input_dir: Path, output_dir: Path) -> dict[str, object]:
    """Validate the supplied feed, filter BEST, and write reproducible outputs."""
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir == input_dir or input_dir in output_dir.parents:
        raise ValueError("Output directory must be outside the raw input directory")

    tables: dict[str, list[dict[str, str]]] = {}
    headers: dict[str, list[str]] = {}
    for filename in SOURCE_FILES:
        if filename == "stop_times.txt":
            headers[filename] = _read_stop_time_header(input_dir / filename)
        else:
            headers[filename], tables[filename] = read_table(
                input_dir / filename, REQUIRED_COLUMNS[filename]
            )

    agencies = unique_index(tables["agency.txt"], "agency_id", "agency.txt")
    routes = unique_index(tables["routes.txt"], "route_id", "routes.txt")
    trips = unique_index(tables["trips.txt"], "trip_id", "trips.txt")
    stops = unique_index(tables["stops.txt"], "stop_id", "stops.txt")
    calendars = unique_index(tables["calendar.txt"], "service_id", "calendar.txt")

    best_agencies = [
        row for row in tables["agency.txt"] if row["agency_id"] == "BEST"
    ]
    if len(best_agencies) != 1:
        raise ValueError(f"Expected exactly one BEST agency; found {len(best_agencies)}")

    invalid_coordinates: list[str] = []
    for stop_id, row in stops.items():
        try:
            latitude = float(row["stop_lat"])
            longitude = float(row["stop_lon"])
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
        except (TypeError, ValueError):
            invalid_coordinates.append(stop_id)
    if invalid_coordinates:
        raise ValueError(
            "Invalid WGS84 coordinates for stop IDs: "
            + ", ".join(invalid_coordinates[:10])
        )

    for route_id, row in routes.items():
        agency_id = row["agency_id"]
        if agency_id not in agencies:
            raise ValueError(
                f"routes.txt route {route_id} references unknown or blank agency_id "
                f"{agency_id!r}"
            )
    for trip_id, row in trips.items():
        if row["route_id"] not in routes:
            raise ValueError(
                f"trips.txt trip {trip_id} references unknown route_id {row['route_id']}"
            )
        if row["service_id"] not in calendars:
            raise ValueError(
                f"trips.txt trip {trip_id} references unknown service_id "
                f"{row['service_id']}"
            )

    best_route_ids = {
        route_id
        for route_id, row in routes.items()
        if row["agency_id"] == "BEST"
    }
    best_trip_ids = {
        trip_id
        for trip_id, row in trips.items()
        if row["route_id"] in best_route_ids
    }
    best_routes = sorted(
        (row for row in tables["routes.txt"] if row["route_id"] in best_route_ids),
        key=lambda row: row["route_id"],
    )
    best_trips = sorted(
        (row for row in tables["trips.txt"] if row["trip_id"] in best_trip_ids),
        key=lambda row: row["trip_id"],
    )
    best_service_ids = {row["service_id"] for row in best_trips}
    best_calendars = sorted(
        (row for row in tables["calendar.txt"] if row["service_id"] in best_service_ids),
        key=lambda row: row["service_id"],
    )

    input_hashes = {
        filename: sha256_file(input_dir / filename) for filename in SOURCE_FILES
    }
    stop_time_rows = 0
    best_stop_time_rows = 0
    chronology_counts = {
        "arrival_after_departure_rows": 0,
        "between_stop_time_decreases": 0,
    }
    late_time_samples: list[str] = []
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="best-gtfs-") as work:
        database_path = Path(work) / "stop_times.sqlite"
        connection = sqlite3.connect(database_path)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute(
            """
            CREATE TABLE stop_times (
                trip_id TEXT NOT NULL,
                stop_sequence INTEGER NOT NULL,
                stop_id TEXT NOT NULL,
                arrival_seconds INTEGER,
                departure_seconds INTEGER,
                row_json TEXT NOT NULL,
                PRIMARY KEY (trip_id, stop_sequence)
            )
            """
        )
        stop_time_path = input_dir / "stop_times.txt"
        batch: list[tuple[str, int, str, int | None, int | None, str]] = []
        try:
            with stop_time_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as source:
                reader = csv.DictReader(source)
                if reader.fieldnames != headers["stop_times.txt"]:
                    raise ValueError("stop_times.txt header changed during processing")
                for raw_row in reader:
                    row = clean_row(raw_row)
                    trip_id = row.get("trip_id", "")
                    stop_id = row.get("stop_id", "")
                    if trip_id not in trips:
                        raise ValueError(
                            f"stop_times.txt references unknown trip_id {trip_id!r}"
                        )
                    if stop_id not in stops:
                        raise ValueError(
                            f"stop_times.txt references unknown stop_id {stop_id!r}"
                        )
                    try:
                        stop_sequence = int(row.get("stop_sequence", ""))
                    except ValueError as error:
                        raise ValueError(
                            f"Invalid stop_sequence for trip {trip_id}: "
                            f"{row.get('stop_sequence')!r}"
                        ) from error
                    if stop_sequence < 0:
                        raise ValueError(
                            f"Negative stop_sequence for trip {trip_id}: {stop_sequence}"
                        )
                    arrival_seconds = parse_gtfs_time(row.get("arrival_time"))
                    departure_seconds = parse_gtfs_time(row.get("departure_time"))
                    batch.append(
                        (
                            trip_id,
                            stop_sequence,
                            stop_id,
                            arrival_seconds,
                            departure_seconds,
                            json.dumps(
                                row, ensure_ascii=False, separators=(",", ":")
                            ),
                        )
                    )
                    stop_time_rows += 1
                    if trip_id in best_trip_ids:
                        best_stop_time_rows += 1
                    if len(batch) >= 20_000:
                        _insert_batch(connection, batch)
                        batch.clear()
                if batch:
                    _insert_batch(connection, batch)
            connection.commit()
        except Exception:
            connection.rollback()
            connection.close()
            raise

        connection.execute(
            "CREATE TEMP TABLE best_trip_ids (trip_id TEXT PRIMARY KEY)"
        )
        connection.executemany(
            "INSERT INTO best_trip_ids (trip_id) VALUES (?)",
            ((trip_id,) for trip_id in sorted(best_trip_ids)),
        )
        chronology_counts, temporal_issue_samples = _scan_chronology(connection)
        pattern_counts: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
        best_stop_ids: set[str] = set()
        trip_stop_counts: list[int] = []
        trip_durations: list[int] = []
        trips_with_late_times = 0
        late_time_rows = 0
        late_time_fields = 0
        max_service_hour: int | None = None
        trips_with_stop_times: set[str] = set()

        with tempfile.TemporaryDirectory(
            prefix=".best-baseline-", dir=output_dir.parent
        ) as staging_name:
            staging_dir = Path(staging_name)
            stop_output = staging_dir / "best_stop_times.csv"
            trip_stop_count_distribution: Counter[int] = Counter()
            with stop_output.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(
                    target,
                    fieldnames=headers["stop_times.txt"],
                    extrasaction="raise",
                    lineterminator="\n",
                )
                writer.writeheader()
                query = connection.execute(
                    """
                    SELECT s.trip_id, s.stop_sequence, s.stop_id,
                           s.arrival_seconds, s.departure_seconds, s.row_json
                    FROM stop_times AS s
                    JOIN best_trip_ids AS b ON b.trip_id = s.trip_id
                    ORDER BY s.trip_id, s.stop_sequence
                    """
                )
                current_trip: str | None = None
                current_stops: list[str] = []
                first_trip_time: int | None = None
                last_trip_time: int | None = None
                current_has_late_time = False

                def finish_trip() -> None:
                    nonlocal current_trip, current_stops
                    nonlocal first_trip_time, last_trip_time, current_has_late_time
                    nonlocal trips_with_late_times
                    if current_trip is None:
                        return
                    trip = trips[current_trip]
                    route_id = trip["route_id"]
                    direction_id = trip.get("direction_id", "")
                    path = tuple(current_stops)
                    pattern_counts[(route_id, direction_id, path)] += 1
                    trips_with_stop_times.add(current_trip)
                    trip_stop_counts.append(len(path))
                    trip_stop_count_distribution[len(path)] += 1
                    if (
                        first_trip_time is not None
                        and last_trip_time is not None
                        and last_trip_time >= first_trip_time
                    ):
                        trip_durations.append(last_trip_time - first_trip_time)
                    if current_has_late_time:
                        trips_with_late_times += 1
                for row in query:
                    trip_id = row[0]
                    if current_trip != trip_id:
                        finish_trip()
                        current_trip = trip_id
                        current_stops = []
                        first_trip_time = None
                        last_trip_time = None
                        current_has_late_time = False
                    stop_id = row[2]
                    arrival_seconds = row[3]
                    departure_seconds = row[4]
                    current_stops.append(stop_id)
                    best_stop_ids.add(stop_id)
                    if first_trip_time is None:
                        first_trip_time = (
                            departure_seconds
                            if departure_seconds is not None
                            else arrival_seconds
                        )
                    last_event_time = (
                        arrival_seconds
                        if arrival_seconds is not None
                        else departure_seconds
                    )
                    if last_event_time is not None:
                        last_trip_time = last_event_time
                    time_values = (arrival_seconds, departure_seconds)
                    row_is_late = any(
                        value is not None and value >= SECONDS_PER_DAY
                        for value in time_values
                    )
                    current_has_late_time = current_has_late_time or row_is_late
                    if row_is_late:
                        late_time_rows += 1
                    for value in time_values:
                        if value is not None:
                            hour = value // 3600
                            max_service_hour = (
                                hour
                                if max_service_hour is None
                                else max(max_service_hour, hour)
                            )
                            if value >= SECONDS_PER_DAY:
                                late_time_fields += 1
                                if len(late_time_samples) < 10:
                                    late_time_samples.append(
                                        parse_time_for_sample(value)
                                    )
                    writer.writerow(json.loads(row[5]))
                finish_trip()

            best_stops = sorted(
                (row for row in tables["stops.txt"] if row["stop_id"] in best_stop_ids),
                key=lambda row: row["stop_id"],
            )
            best_agency_rows = sorted(best_agencies, key=lambda row: row["agency_id"])
            write_csv(
                staging_dir / "best_agencies.csv",
                headers["agency.txt"],
                best_agency_rows,
            )
            write_csv(staging_dir / "best_routes.csv", headers["routes.txt"], best_routes)
            write_csv(staging_dir / "best_trips.csv", headers["trips.txt"], best_trips)
            write_csv(
                staging_dir / "best_calendar.csv",
                headers["calendar.txt"],
                best_calendars,
            )
            write_csv(staging_dir / "best_stops.csv", headers["stops.txt"], best_stops)

            route_by_id = routes
            patterns: list[dict[str, object]] = []
            for (route_id, direction_id, path), trip_count in pattern_counts.items():
                canonical = json.dumps(
                    [route_id, direction_id, path],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                pattern_id = "BEST-" + hashlib.sha256(
                    canonical.encode("utf-8")
                ).hexdigest()[:16]
                route = route_by_id[route_id]
                patterns.append(
                    {
                        "pattern_id": pattern_id,
                        "route_id": route_id,
                        "route_short_name": route.get("route_short_name", ""),
                        "route_long_name": route.get("route_long_name", ""),
                        "direction_id": direction_id,
                        "trip_count": trip_count,
                        "stop_count": len(path),
                        "stop_ids_json": json.dumps(
                            list(path), ensure_ascii=False, separators=(",", ":")
                        ),
                    }
                )
            patterns.sort(
                key=lambda row: (
                    str(row["route_id"]),
                    str(row["direction_id"]),
                    str(row["pattern_id"]),
                )
            )
            write_csv(
                staging_dir / "route_patterns.csv",
                (
                    "pattern_id",
                    "route_id",
                    "route_short_name",
                    "route_long_name",
                    "direction_id",
                    "trip_count",
                    "stop_count",
                    "stop_ids_json",
                ),
                patterns,
            )

            source_counts = {
                "agencies": len(agencies),
                "routes": len(routes),
                "trips": len(trips),
                "stops": len(stops),
                "stop_time_rows": stop_time_rows,
                "calendar_services": len(calendars),
            }
            best_counts = {
                "agencies": len(best_agencies),
                "routes": len(best_routes),
                "trips": len(best_trips),
                "trips_with_stop_times": len(trips_with_stop_times),
                "trips_without_stop_times": len(best_trip_ids - trips_with_stop_times),
                "stops_served": len(best_stops),
                "stop_time_rows": best_stop_time_rows,
                "calendar_services": len(best_calendars),
                "route_patterns": len(patterns),
            }
            feed_info = tables["feed_info.txt"][0] if tables["feed_info.txt"] else {}
            duration_summary = summarize(trip_durations)
            duration_summary["zero_duration_trip_count"] = sum(
                duration == 0 for duration in trip_durations
            )
            metrics: dict[str, object] = {
                "analysis": {
                    "name": "BEST-only scheduled route-pattern baseline",
                    "version": "1.0.0",
                    "selection_rule": (
                        "Select routes with routes.agency_id equal to BEST, then "
                        "select trips whose route_id is in that route set."
                    ),
                    "pattern_rule": (
                        "A pattern is an exact ordered stop_id sequence within "
                        "route_id and direction_id; blank direction_id is retained "
                        "as blank."
                    ),
                    "time_rule": (
                        "Parse GTFS HH:MM:SS to seconds without wrapping at 24 hours. "
                        "Times at or after 24:00:00 remain on the GTFS service-day axis."
                    ),
                },
                "source": {
                    "feed_publisher_name": feed_info.get("feed_publisher_name", ""),
                    "feed_publisher_url": feed_info.get("feed_publisher_url", ""),
                    "declared_feed_start_date": feed_info.get("feed_start_date", ""),
                    "declared_feed_end_date": feed_info.get("feed_end_date", ""),
                    "sha256": input_hashes,
                },
                "scope": {
                    "agency_id": "BEST",
                    "source_counts": source_counts,
                    "best_counts": best_counts,
                    "excluded_counts": {
                        "routes": len(routes) - len(best_routes),
                        "trips": len(trips) - len(best_trips),
                    },
                },
                "trip_stop_count": summarize(trip_stop_counts),
                "trip_duration_seconds": duration_summary,
                "service_time": {
                    "time_fields_at_or_after_24h": late_time_fields,
                    "stop_time_rows_with_any_time_at_or_after_24h": late_time_rows,
                    "trips_with_any_time_at_or_after_24h": trips_with_late_times,
                    "maximum_gtfs_hour": max_service_hour,
                    "sample_times_at_or_after_24h": late_time_samples,
                },
                "trip_stop_count_distribution": {
                    str(stop_count): count
                    for stop_count, count in sorted(
                        trip_stop_count_distribution.items()
                    )
                },
                "pattern_trip_count_distribution": {
                    str(trips_per_pattern): pattern_count
                    for trips_per_pattern, pattern_count in sorted(
                        Counter(pattern_counts.values()).items()
                    )
                },
                "validation": {
                    "structural_checks_passed": True,
                    "checked_unique_keys": [
                        "agency.agency_id",
                        "routes.route_id",
                        "trips.trip_id",
                        "stops.stop_id",
                        "calendar.service_id",
                        "stop_times.(trip_id, stop_sequence)",
                    ],
                    "foreign_key_orphans": 0,
                    "invalid_coordinate_count": 0,
                    "stop_time_rows_checked": stop_time_rows,
                    "invalid_time_values": 0,
                    "temporal_order_is_valid": (
                        chronology_counts["arrival_after_departure_rows"] == 0
                        and chronology_counts["between_stop_time_decreases"] == 0
                    ),
                    **chronology_counts,
                    "temporal_issue_samples": temporal_issue_samples,
                },
                "interpretation_limits": [
                    "GTFS describes scheduled service, not observed running time or passenger demand.",
                    "Exact stop-sequence patterns do not establish route geometry because shapes.txt was not supplied.",
                    "Route and trip counts are descriptive baselines, not passenger-benefit or operational-feasibility estimates.",
                    "The input audit identifies BLRTransit as publisher; this pipeline does not establish official operator provenance or licensing.",
                ],
            }
            metrics_path = staging_dir / "baseline_metrics.json"
            metrics_path.write_text(
                json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            output_dir.mkdir(parents=True, exist_ok=True)
            for staged_file in sorted(staging_dir.iterdir()):
                if staged_file.is_file():
                    os.replace(staged_file, output_dir / staged_file.name)

        connection.close()
    return metrics


def _insert_batch(
    connection: sqlite3.Connection,
    batch: Sequence[tuple[str, int, str, int | None, int | None, str]],
) -> None:
    try:
        connection.executemany(
            """
            INSERT INTO stop_times
                (trip_id, stop_sequence, stop_id, arrival_seconds,
                 departure_seconds, row_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
    except sqlite3.IntegrityError as error:
        raise ValueError(
            "Duplicate stop_times (trip_id, stop_sequence) key detected"
        ) from error


def _scan_chronology(
    connection: sqlite3.Connection,
) -> tuple[dict[str, int], list[dict[str, str]]]:
    totals = {
        "arrival_after_departure_rows": 0,
        "between_stop_time_decreases": 0,
    }
    samples: list[dict[str, str]] = []
    current_trip: str | None = None
    records: list[tuple[int | None, int | None]] = []

    def finish_trip(trip_id: str | None) -> None:
        if trip_id is None:
            return
        issues = chronology_issues(records)
        for name, count in issues.items():
            totals[name] += count
            if count and len(samples) < 10:
                samples.append({"trip_id": trip_id, "issue": name, "count": str(count)})

    for trip_id, arrival, departure in connection.execute(
        """
        SELECT trip_id, arrival_seconds, departure_seconds
        FROM stop_times
        ORDER BY trip_id, stop_sequence
        """
    ):
        if current_trip != trip_id:
            finish_trip(current_trip)
            current_trip = trip_id
            records = []
        records.append((arrival, departure))
    finish_trip(current_trip)
    return totals, samples


def parse_time_for_sample(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Filter the supplied GTFS feed to BEST and build a route-pattern baseline."
    )
    parser.add_argument("--input", type=Path, default=project_root / "data" / "raw")
    parser.add_argument(
        "--output", type=Path, default=project_root / "data" / "processed" / "best"
    )
    args = parser.parse_args()
    try:
        metrics = build_baseline(args.input, args.output)
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(metrics["scope"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
