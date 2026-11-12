from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_best_baseline import (  # noqa: E402
    build_baseline,
    chronology_issues,
    parse_gtfs_time,
)
from qualify_best_baseline import classify_duration, qualify_baseline  # noqa: E402


def write_table(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class GtfsTimeTests(unittest.TestCase):
    def test_hours_beyond_24_are_kept_on_the_service_day_axis(self) -> None:
        self.assertEqual(parse_gtfs_time("24:00:00"), 86_400)
        self.assertEqual(parse_gtfs_time("25:02:03"), 90_123)
        self.assertEqual(parse_gtfs_time("123:59:59"), 446_399)
        self.assertIsNone(parse_gtfs_time(""))

    def test_malformed_time_is_rejected(self) -> None:
        for value in ("25:60:00", "12:00", "-1:00:00", "ab:00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_gtfs_time(value)

    def test_chronology_uses_extended_hours_without_wrapping(self) -> None:
        result = chronology_issues(
            [
                (parse_gtfs_time("23:55:00"), parse_gtfs_time("23:57:00")),
                (parse_gtfs_time("24:10:00"), parse_gtfs_time("24:12:00")),
            ]
        )
        self.assertEqual(
            result,
            {"arrival_after_departure_rows": 0, "between_stop_time_decreases": 0},
        )

    def test_chronology_flags_a_decrease(self) -> None:
        result = chronology_issues(
            [
                (parse_gtfs_time("24:10:00"), parse_gtfs_time("24:12:00")),
                (parse_gtfs_time("24:05:00"), parse_gtfs_time("24:06:00")),
            ]
        )
        self.assertEqual(result["between_stop_time_decreases"], 1)


class BestBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        self._write_fixture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_fixture(self) -> None:
        write_table(
            self.raw / "agency.txt",
            ["agency_id", "agency_name", "agency_url", "agency_timezone"],
            [
                {
                    "agency_id": "BEST",
                    "agency_name": "BEST",
                    "agency_url": "https://example.test/best",
                    "agency_timezone": "Asia/Kolkata",
                },
                {
                    "agency_id": "TMT",
                    "agency_name": "TMT",
                    "agency_url": "https://example.test/tmt",
                    "agency_timezone": "Asia/Kolkata",
                },
            ],
        )
        write_table(
            self.raw / "routes.txt",
            ["route_id", "agency_id", "route_type", "route_short_name", "route_long_name"],
            [
                {
                    "route_id": "r-best",
                    "agency_id": "BEST",
                    "route_type": "3",
                    "route_short_name": "A",
                    "route_long_name": "BEST test route",
                },
                {
                    "route_id": "r-tmt",
                    "agency_id": "TMT",
                    "route_type": "3",
                    "route_short_name": "T",
                    "route_long_name": "TMT test route",
                },
            ],
        )
        write_table(
            self.raw / "trips.txt",
            ["route_id", "service_id", "trip_id", "direction_id"],
            [
                {"route_id": "r-best", "service_id": "svc", "trip_id": "t1", "direction_id": "0"},
                {"route_id": "r-best", "service_id": "svc", "trip_id": "t2", "direction_id": "0"},
                {"route_id": "r-best", "service_id": "svc", "trip_id": "t3", "direction_id": "0"},
                {"route_id": "r-tmt", "service_id": "svc", "trip_id": "t4", "direction_id": "0"},
            ],
        )
        write_table(
            self.raw / "stops.txt",
            ["stop_id", "stop_name", "stop_lat", "stop_lon"],
            [
                {"stop_id": "s1", "stop_name": "One", "stop_lat": "19.0", "stop_lon": "72.8"},
                {"stop_id": "s2", "stop_name": "Two", "stop_lat": "19.1", "stop_lon": "72.9"},
                {"stop_id": "s3", "stop_name": "Three", "stop_lat": "19.2", "stop_lon": "73.0"},
                {"stop_id": "s4", "stop_name": "Four", "stop_lat": "19.3", "stop_lon": "73.1"},
            ],
        )
        write_table(
            self.raw / "calendar.txt",
            [
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
            ],
            [
                {
                    "service_id": "svc",
                    "monday": "1",
                    "tuesday": "1",
                    "wednesday": "1",
                    "thursday": "1",
                    "friday": "1",
                    "saturday": "1",
                    "sunday": "1",
                    "start_date": "20260819",
                    "end_date": "20270215",
                }
            ],
        )
        write_table(
            self.raw / "feed_info.txt",
            [
                "feed_publisher_name",
                "feed_publisher_url",
                "feed_lang",
                "feed_start_date",
                "feed_end_date",
            ],
            [
                {
                    "feed_publisher_name": "Test publisher",
                    "feed_publisher_url": "https://example.test",
                    "feed_lang": "en",
                    "feed_start_date": "20260819",
                    "feed_end_date": "20270215",
                }
            ],
        )
        write_table(
            self.raw / "stop_times.txt",
            [
                "trip_id",
                "arrival_time",
                "departure_time",
                "stop_id",
                "stop_sequence",
                "timepoint",
            ],
            [
                {"trip_id": "t1", "arrival_time": "23:50:00", "departure_time": "23:55:00", "stop_id": "s1", "stop_sequence": "1", "timepoint": "1"},
                {"trip_id": "t1", "arrival_time": "24:10:00", "departure_time": "24:15:00", "stop_id": "s2", "stop_sequence": "2", "timepoint": "1"},
                {"trip_id": "t2", "arrival_time": "24:50:00", "departure_time": "24:55:00", "stop_id": "s1", "stop_sequence": "1", "timepoint": "1"},
                {"trip_id": "t2", "arrival_time": "25:10:00", "departure_time": "25:15:00", "stop_id": "s2", "stop_sequence": "2", "timepoint": "1"},
                {"trip_id": "t3", "arrival_time": "07:00:00", "departure_time": "07:01:00", "stop_id": "s1", "stop_sequence": "1", "timepoint": "1"},
                {"trip_id": "t3", "arrival_time": "07:10:00", "departure_time": "07:10:00", "stop_id": "s3", "stop_sequence": "2", "timepoint": "1"},
                {"trip_id": "t4", "arrival_time": "08:00:00", "departure_time": "08:01:00", "stop_id": "s4", "stop_sequence": "1", "timepoint": "1"},
            ],
        )

    def test_filters_best_rebuilds_patterns_and_is_deterministic(self) -> None:
        first = self.root / "out-one"
        second = self.root / "out-two"
        metrics = build_baseline(self.raw, first)
        build_baseline(self.raw, second)

        best = metrics["scope"]["best_counts"]
        self.assertEqual(best["agencies"], 1)
        self.assertEqual(best["routes"], 1)
        self.assertEqual(best["trips"], 3)
        self.assertEqual(best["stops_served"], 3)
        self.assertEqual(best["stop_time_rows"], 6)
        self.assertEqual(best["route_patterns"], 2)
        self.assertEqual(metrics["trip_stop_count_distribution"], {"2": 3})
        self.assertEqual(metrics["pattern_trip_count_distribution"], {"1": 1, "2": 1})
        self.assertEqual(
            metrics["trip_duration_seconds"]["zero_duration_trip_count"], 0
        )

        late = metrics["service_time"]
        self.assertEqual(late["time_fields_at_or_after_24h"], 6)
        self.assertEqual(late["stop_time_rows_with_any_time_at_or_after_24h"], 3)
        self.assertEqual(late["trips_with_any_time_at_or_after_24h"], 2)
        self.assertEqual(late["maximum_gtfs_hour"], 25)
        self.assertTrue(metrics["validation"]["temporal_order_is_valid"])

        with (first / "best_trips.csv").open(encoding="utf-8", newline="") as source:
            best_trip_ids = {row["trip_id"] for row in csv.DictReader(source)}
        self.assertEqual(best_trip_ids, {"t1", "t2", "t3"})

        with (first / "route_patterns.csv").open(encoding="utf-8", newline="") as source:
            patterns = list(csv.DictReader(source))
        self.assertEqual(sorted(int(row["trip_count"]) for row in patterns), [1, 2])
        self.assertEqual(
            {tuple(json.loads(row["stop_ids_json"])) for row in patterns},
            {("s1", "s2"), ("s1", "s3")},
        )

        first_files = {p.name: p.read_bytes() for p in first.iterdir()}
        second_files = {p.name: p.read_bytes() for p in second.iterdir()}
        self.assertEqual(first_files, second_files)

    def test_quality_audit_classifies_zero_and_post_midnight_trips(self) -> None:
        path = self.raw / "stop_times.txt"
        with path.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
            headers = rows[0].keys()
        for row in rows:
            if row["trip_id"] == "t3":
                row["arrival_time"] = "07:01:00"
                row["departure_time"] = "07:01:00"
        write_table(path, list(headers), rows)

        baseline = self.root / "baseline"
        metrics = build_baseline(self.raw, baseline)
        self.assertEqual(
            classify_duration(10, 10, {10}), "zero_duration_one_distinct_time"
        )
        self.assertEqual(
            classify_duration(10, 10, {9, 10, 11}),
            "zero_duration_endpoint_variation",
        )
        self.assertEqual(
            classify_duration(None, 10, {10}), "duration_unavailable"
        )

        first = baseline / "qualification-one"
        second = baseline / "qualification-two"
        summary = qualify_baseline(self.raw, baseline, first)
        qualify_baseline(self.raw, baseline, second)

        self.assertEqual(summary["scope"]["stop_time_rows"], 6)
        self.assertEqual(summary["duration_quality"]["zero_duration_trip_count"], 1)
        self.assertEqual(
            summary["duration_quality"]["trips_by_classification"],
            {"positive_duration": 2, "zero_duration_one_distinct_time": 1},
        )
        self.assertEqual(
            summary["post_midnight_quality"]["trips_with_any_time_at_or_after_24h"],
            2,
        )
        self.assertEqual(
            summary["post_midnight_quality"]["stop_time_rows_with_any_time_at_or_after_24h"],
            3,
        )
        self.assertEqual(summary["cross_check"]["exact_route_label_matches"], [])

        with (first / "zero_duration_trips.csv").open(
            encoding="utf-8", newline=""
        ) as source:
            zero_trips = list(csv.DictReader(source))
        self.assertEqual([row["trip_id"] for row in zero_trips], ["t3"])
        self.assertEqual(
            zero_trips[0]["classification"], "zero_duration_one_distinct_time"
        )

        first_files = {item.name: item.read_bytes() for item in first.iterdir()}
        second_files = {item.name: item.read_bytes() for item in second.iterdir()}
        self.assertEqual(first_files, second_files)

    def test_unknown_stop_reference_fails(self) -> None:
        path = self.raw / "stop_times.txt"
        with path.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
            headers = rows[0].keys()
        rows[0]["stop_id"] = "missing-stop"
        write_table(path, list(headers), rows)
        output = self.root / "bad-output"
        with self.assertRaisesRegex(ValueError, "unknown stop_id"):
            build_baseline(self.raw, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
