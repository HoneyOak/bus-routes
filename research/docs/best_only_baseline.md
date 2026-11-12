# BEST-only baseline milestone

## Purpose and scope

This milestone establishes a reproducible descriptive baseline for BEST within the supplied Greater Mumbai multi-operator GTFS feed. The supplied audit lists BEST, TMT, KDMT, and VVMT, and identifies BLRTransit as the feed publisher. The analysis selects routes whose agency_id is BEST, then selects trips attached to those routes. It derives the stops used by those trips and keeps only calendar services referenced by them.

The raw feed is retained under data/raw/. Processing writes only to data/processed/best/.

## Reproduce

Requires Python 3.10 or newer and the Python standard library only.

Run the processor: python scripts/build_best_baseline.py
Run the unit tests: python -m unittest discover -s tests -v

Optional paths: python scripts/build_best_baseline.py --input data/raw --output data/processed/best

Generated outputs are sorted by stable identifiers and sequence, use UTF-8 with LF line endings, and include SHA-256 digests of all seven raw inputs in baseline_metrics.json. Re-running the script with the same inputs should reproduce identical output bytes.

## Filtering and pattern method

- BEST is selected by the exact agency_id value BEST in routes.txt.
- A trip is included when its route_id belongs to that selected route set.
- A route pattern is an exact ordered stop_id sequence grouped by route_id and direction_id. Blank direction values remain blank. The pattern ID is a stable SHA-256 prefix derived from those values and the ordered stop IDs.
- Stop times are sorted by trip_id and numeric stop_sequence in derived files. The source files remain unchanged.
- GTFS times are parsed as elapsed seconds from the service-day origin. Hours greater than 23 are retained as written; they are never wrapped to the next clock day. Values at or after 24:00:00 are counted in the metrics.
- Scheduled trip duration is calculated from the first available departure (or arrival) to the last available arrival (or departure). It is a schedule-based descriptor, not observed travel time.

## Validation

The pipeline checks required columns, duplicate agency/route/trip/stop/service identifiers, route-to-agency, trip-to-route, trip-to-calendar, stop-time-to-trip, and stop-time-to-stop references, valid WGS84 stop coordinates, nonnegative integer stop sequences, unique (trip_id, stop_sequence) keys, time syntax, and time order within and between stops. Structural/key/time-format errors stop processing. Time-order anomalies are counted and sampled in baseline_metrics.json so they remain visible.

The unit tests cover GTFS times beyond 24:00, malformed times, chronology, BEST-only selection, repeated versus distinct patterns, output determinism, and an invalid stop reference.

## Outputs

- best_agencies.csv, best_routes.csv, best_trips.csv, and best_calendar.csv: selected source rows.
- best_stops.csv: stops served by selected trips.
- best_stop_times.csv: selected stop-time rows sorted by trip and sequence.
- route_patterns.csv: one row per exact route/direction/stop-sequence pattern, with the ordered stop IDs stored as JSON.
- baseline_metrics.json: source hashes, scope counts, time and trip-stop descriptors, validation results, and interpretation limits.

## Research limits and next steps

This is an input and network-description milestone, not an optimization result. GTFS does not provide passenger demand, observed running times, onboard loads, vehicle capacity, operating cost, or equity outcomes. The supplied archive also lacks shapes.txt and calendar_dates.txt, so this step cannot reconstruct route geometry or evaluate date exceptions. Exact stop-sequence patterns are not evidence of a mapped path.

Before making passenger-benefit or feasibility claims, establish feed provenance and licensing, obtain or validate shapes.txt and service exceptions, define the study boundary, and collect independent demand, running-time, capacity, and operating-cost evidence. Subsequent optimization should compare passenger access and transfer impacts with service quantity, cost, and geographic equity using explicit constraints.
## Snapshot findings

The current supplied snapshot yields 937 BEST routes, 91,129 BEST trips, 5,802 served stops, and 887 exact route patterns. The feed-wide time-format and chronology checks pass across 2,655,026 stop-time rows. Of the BEST trips, 549 contain service times at or after 24:00:00. The calculated scheduled duration is zero seconds for 2,124 trips; inspect those records before using duration summaries in downstream analysis. These figures describe the supplied BLRTransit feed and do not establish official provenance.
A spot check of five zero-duration trips found eight stop-time rows per trip and identical first and last times. The monotonicity checks pass, so this appears as a scheduled-duration data-quality issue rather than a time-order failure; do not interpret these values as actual running times.
