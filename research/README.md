# BEST-only Mumbai GTFS research track

This folder holds the reproducible descriptive baseline and data-quality work supporting the Mumbai bus-route research. It is separate from the route-optimizer prototype in the repository root.

## Scope

The pipeline filters a multi-operator Greater Mumbai GTFS snapshot to agency_id BEST, reconstructs deterministic exact stop-sequence patterns, validates GTFS structure and times beyond 24:00, and reports baseline quality findings. It does not establish passenger demand, observed running time, capacity, cost, equity impact, or operational feasibility.

The working snapshot names BLRTransit in feed_info.txt and declares dates 2026-08-19 through 2027-02-15. It contains BEST, TMT, KDMT, and VVMT records. Its exact upstream file version and license scope remain unconfirmed; see docs/data_provenance.md.

## Data handling

Raw GTFS files, the local audit ZIP, and generated tables are not included in this repository. The research data folder is ignored by Git. Obtain an authorized snapshot, place its seven supplied GTFS text files under data/raw/, and preserve those inputs unchanged. The source registry records the local archive fingerprint and evidence status.

## Reproduce

Use Python 3.10 or newer and the standard library. From this research directory, run:

    python ingest_gtfs.py
    python scripts/build_best_baseline.py
    python scripts/qualify_best_baseline.py
    python -m unittest discover -s tests -v

The ingestion outputs go under data/processed/. The BEST baseline and qualification outputs are generated under data/processed/best/. Raw inputs and generated data remain untracked.

## Method and limits

- Route patterns are exact ordered stop_id sequences grouped by route_id and direction_id.
- GTFS times remain on the service-day axis; 24:00:00 and later are not wrapped to clock time.
- Schedule-derived durations are not observed running times.
- Missing shapes.txt and calendar_dates.txt limit geometry and service-exception analysis.
- The current feed is exploratory until its exact source, license, completeness, and dated operator schedule checks are established.

See docs/best_only_baseline.md, docs/baseline_qualification.md, and docs/data_provenance.md.

## Schedule-reference pilot

The first source comparison is a secondary check of route 321 LTD against an attributed copy of a BEST schedule carried by Chalo. The route label and timetable date are not exact matches, and the comparison is partial. It is not operator validation.

The input extract and source metadata are in data/references/. With the BEST baseline built, run:

    python scripts/compare_best_schedule.py

The tool checks the baseline hashes when raw files are available, filters service for the comparison date, and writes the time-by-time CSV and JSON summary under data/processed/best/qualification/. See docs/schedule_reference_review.md for the results and next gate.

The user-supplied BEST Prawas route-map views confirm endpoint labels for the zero-duration routes 394 AS and 397 AS. They show no timetable times; see docs/schedule_reference_review.md and data/references/best_prawas_route_maps.json.

## BEST timetable evidence update (2026-11-23)

The user supplied 51 BEST Prawas screenshots for route 394 AS, direction Kannamwar Nagar No.2 to Vikhroli Bus Station (E), with selected date 23-Nov-2026. Deduplication and origin-label filtering yield 333 distinct visible departures from 05:50 to 22:50. The median gap is 3 minutes, with gaps from 1 to 10 minutes; headways are variable. Of these distinct times, 220 overlap candidate GTFS direction BEST_2898; 113 Prawas times are absent from the candidate, while 81 candidate GTFS times are not seen in the screenshots. Screenshot completeness and schedule effective date remain unconfirmed. Source images are archived locally and excluded from GitHub.

A Google Maps itinerary labeled A-397 shows origin stop ID 14227 and the first ten stops of candidate BEST_2901 / 397 AS direction 0 in the same order through Janata Market. Its route headsign mentions Building No.124, but the explicit stop list ends at Janata Market. The screenshot says Monday without a calendar date. See [the schedule reference review](docs/schedule_reference_review.md) and the [machine-readable evidence](data/references/best_route_schedule_observations_2026-11-23.json). These schedule comparisons do not establish passenger demand, actual running time, or operating feasibility.

## Feed source decision (2026-11-24)

BEST Prawas is selected as the primary operator timetable reference because its Google Play listing displays developer name THE BEST, describes the app as developed by BEST Undertaking, and lists static timetables for each route. No public operator-issued BEST GTFS download was located; the available BLRTransit snapshot remains exploratory. For the 23-Nov-2026 394 AS comparison, 220 of 333 distinct Prawas departures overlap the candidate GTFS (66.1%). The candidate marks that date active in its declared calendar, but this does not establish schedule currency. Its 301 trips for the compared direction have zero scheduled duration. Keep the feed for route-pattern exploration, not operational schedule optimization. See [the source-selection and effectiveness review](docs/schedule_reference_review.md).
