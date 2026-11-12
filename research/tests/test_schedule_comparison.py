import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from compare_best_schedule import (  # noqa: E402
    compare_schedule_reference,
    parse_gtfs_time,
)


class ScheduleComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.baseline = self.root / "baseline"
        self.baseline.mkdir()
        self.references = self.root / "references"
        self.references.mkdir()
        self.metadata_path = self.references / "metadata.json"
        self.reference_csv = self.references / "departures.csv"
        self.output = self.root / "output"
        self._write_csv(
            self.baseline / "best_routes.csv",
            ["route_id", "agency_id", "route_short_name", "route_long_name"],
            [["R1", "BEST", "1", "Origin to Destination"]],
        )
        self._write_csv(
            self.baseline / "best_trips.csv",
            ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id"],
            [
                ["R1", "SVC", "T1", "Destination", "0"],
                ["R1", "SVC", "T2", "Destination", "0"],
                ["R1", "SVC", "T3", "Destination", "0"],
            ],
        )
        self._write_csv(
            self.baseline / "best_calendar.csv",
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
            [["SVC", "1", "1", "1", "1", "1", "1", "1", "20260819", "20270215"]],
        )
        self._write_csv(
            self.baseline / "best_stop_times.csv",
            [
                "trip_id",
                "arrival_time",
                "departure_time",
                "stop_id",
                "stop_sequence",
            ],
            [
                ["T1", "05:03:00", "05:03:00", "S1", "1"],
                ["T1", "05:30:00", "05:30:00", "S2", "2"],
                ["T2", "06:05:00", "06:05:00", "S1", "1"],
                ["T2", "06:35:00", "06:35:00", "S2", "2"],
                ["T3", "25:15:00", "25:15:00", "S1", "1"],
                ["T3", "25:50:00", "25:50:00", "S2", "2"],
            ],
        )
        (self.baseline / "baseline_metrics.json").write_text(
            json.dumps(
                {
                    "source": {
                        "feed_publisher_name": "BLRTransit",
                        "declared_feed_start_date": "20260819",
                        "declared_feed_end_date": "20270215",
                        "sha256": {},
                    }
                }
            ),
            encoding="utf-8",
        )
        metadata = {
            "schema_version": 1,
            "reference_id": "fixture",
            "source_name": "fixture",
            "source_url": "https://example.test/timetable",
            "source_data_retrieved_from_chalo": "2026-10-16",
            "observed_on": "2026-11-12",
            "reference_route_label": "1",
            "reference_origin_stop": "Origin",
            "reference_service_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "service_date_compared": "2026-10-16",
            "gtfs_route_id": "R1",
            "gtfs_route_short_name": "1",
            "gtfs_direction_id": "0",
            "gtfs_origin_stop_id": "S1",
        }
        self.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        self._write_csv(
            self.reference_csv,
            ["departure_time"],
            [["05:03:00"], ["06:30:00"], ["25:15:00"]],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target, lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows)

    def test_gtfs_time_after_24_hours_is_preserved(self) -> None:
        self.assertEqual(parse_gtfs_time("25:15:00"), 90_900)

    def test_comparison_counts_overlap_and_unmatched_departures(self) -> None:
        summary = compare_schedule_reference(
            self.baseline,
            self.reference_csv,
            self.metadata_path,
            self.output,
        )
        comparison = summary["comparison"]
        self.assertEqual(comparison["status"], "partial")
        self.assertEqual(comparison["matched_departure_count"], 2)
        self.assertEqual(comparison["reference_only_times"], ["06:30:00"])
        self.assertEqual(comparison["gtfs_only_times"], ["06:05:00"])
        self.assertEqual(comparison["reference_departure_count"], 3)
        self.assertEqual(comparison["gtfs_departure_count"], 3)
        self.assertTrue((self.output / "departure_comparison.csv").is_file())
        self.assertTrue((self.output / "comparison.json").is_file())

    def test_rejects_reference_day_outside_service_days(self) -> None:
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        metadata["reference_service_days"] = ["Monday"]
        self.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside the reference service days"):
            compare_schedule_reference(
                self.baseline,
                self.reference_csv,
                self.metadata_path,
                self.output,
            )

    def test_refuses_to_overwrite_existing_comparison(self) -> None:
        self.output.mkdir()
        (self.output / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            compare_schedule_reference(
                self.baseline,
                self.reference_csv,
                self.metadata_path,
                self.output,
            )
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()

