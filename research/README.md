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

