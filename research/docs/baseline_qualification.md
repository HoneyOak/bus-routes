# BEST baseline qualification

## Purpose

This phase checks whether the supplied BEST schedule fields are suitable for later service and passenger-impact analysis. It reuses the baseline outputs only when their recorded raw-input hashes match the preserved data/raw/ snapshot.

Run the baseline builder first, then run: python scripts/qualify_best_baseline.py

The quality report is written to data/processed/best/qualification/. The tests can be run with: python -m unittest discover -s tests -v

## Findings for this snapshot

- The audit covered 91,129 BEST trips, 937 route IDs, 887 exact route patterns, and 2,431,236 BEST stop-time rows.
- 2,124 trips (2.3308%) calculate to zero seconds from first available departure/arrival to last available arrival/departure. Every one has exactly one distinct nonblank time value across its stop-time fields. None of the BEST stop-time arrival/departure fields are blank.
- The zero-duration trips are concentrated in 20 route IDs and 20 patterns. Every trip on each affected route has this zero-duration result. Examples include routes 394 AS, 397 AS, 370, and 910 AS/LTD. This pattern suggests a systematic schedule-time encoding issue in those route records; it is not evidence that the trips take no time.
- 549 trips cross midnight: each starts before 24:00 and has a final scheduled time at or after 24:00. They account for 12,367 stop-time rows with at least one such time and 24,734 extended-hour arrival/departure fields. The latest hour is 25.
- Time values remain ordered across all trips. The first baseline validation also found no malformed times, duplicate trip/sequence keys, foreign-key orphans, or invalid stop coordinates.
- Five sampled zero-duration trips each had eight stop-time rows and the same first and last time. The full trip-level details are in zero_duration_trips.csv.

## Official-source cross-check

BEST's official [Bandra Kurla Complex Routes (Air Conditioned) PDF](https://www.bestundertaking.com/assets/pdf/mmrconnect.pdf) lists BKC route labels, trip times, frequency, and itineraries. Its labels (BKC-10 through BKC-13 and BKC-21 through BKC-25) have no exact match in this feed's BEST route_short_name values. The document's effective date was not identifiable in the PDF text reviewed. It therefore cannot validate the schedules in this snapshot; it is recorded as a limited reference only.

## Generated files

- zero_duration_trips.csv: trip-level details and classification for every zero-duration schedule.
- post_midnight_trips.csv: the 549 extended-hour trips with start/end, route, pattern, and stop counts.
- route_quality.csv: duration and midnight metrics grouped by route ID.
- route_pattern_quality.csv: the same metrics grouped by reconstructed route pattern.
- baseline_quality_summary.json: counts, raw hashes, classifications, cross-check result, and consistency checks.

## Decision

Treat the current feed as exploratory. Keep its schedule-duration values out of running-time or passenger-benefit claims until the affected routes are checked against an authoritative schedule with a matching effective date. Before publication or government presentation, establish the feed's source, license, update history, and completeness. The official PDF cross-check did not establish those items.

## Secondary-source timetable pilot

A separate route 321 LTD check is documented in docs/schedule_reference_review.md. It compares only first-stop departures with a dated secondary copy attributed to Chalo. The overlap is partial and does not establish official schedule accuracy. The primary-source validation gate remains open.

## BEST Prawas route-map evidence

User-supplied BEST Prawas screenshots show route labels and terminals for 394 AS and 397 AS that correspond to the GTFS route names and endpoints. This helps identify the candidate route records: BEST_2898/BEST_2899 for 394 AS and BEST_2900/BEST_2901 for 397 AS.

The quality report still flags every trip on these routes as zero-duration: 600 of 600 trips for 394 AS and 668 of 668 for 397 AS. The screenshots are map views with no departure times or effective date, so they do not validate the schedule values. See docs/schedule_reference_review.md.

## Prawas timetable and reverse-route sequence evidence (2026-11-23)

The user supplied a partial 394 AS Prawas timetable for Kannamwar Nagar No.2 to Vikhroli Bus Station (E), selected date 2026-11-23. Eleven of 16 visible departures match candidate GTFS direction BEST_2898; five do not. The visible first and last times match the feed extrema, but the incomplete screenshots do not support a full timetable comparison. All 301 candidate GTFS trips still have one repeated time value across all eight stops, so only the origin departures can be compared.

A user-transcribed Google Maps sequence labelled 397 A follows the interior stop order of candidate GTFS 397 AS direction BEST_2901 from Kinnari Hall through Janata Market. The label differs, some GTFS stops are omitted, the GTFS terminal is not shown, and the Google Maps date/artifact is unavailable. The GTFS candidate repeats one time at all 11 stops. See [schedule_reference_review.md](schedule_reference_review.md) and the machine-readable [observation record](../data/references/best_route_schedule_observations_2026-11-23.json). Keep schedule-derived duration out of running-time and passenger-benefit claims.
