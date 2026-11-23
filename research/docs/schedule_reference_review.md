# Preliminary BEST timetable cross-check

Review date: 2026-11-12

## Decision

The route 321 comparison is a partial secondary-source check. It is useful as a reproducible warning that the supplied GTFS and the schedule copy do not agree exactly. It does not validate the GTFS as an official, complete, or accurate BEST feed. Keep the current feed exploratory.

## Reference and limitations

The reviewed airportbus.in page labels the service 321 from Mahim Bus Station to CSMIA Terminal 2 and says the route continues to Barve Nagar. Its data-source page says the displayed Mumbai departures are BEST schedules carried by Chalo, retrieved 2026-10-16. It also says only the first stop is timetabled on the route page; intermediate times are estimated. airportbus.in states that it is not affiliated with BEST or the airport.

The official BEST Prawas app listing describes a static timetable for each route. A dated timetable from that app was not available in the reviewed web sources, so the comparison below remains a secondary copy of schedule information attributed to Chalo.

The reference CSV preserves the 33 Monday-to-Saturday departures shown for Mahim Bus Station. Its metadata records the page URL, the page's stated Chalo retrieval date, our observation date, and limitations. The route page does not state a schedule effective date.

## Candidate route mapping

The supplied BEST baseline contains route BEST_1933, labelled 321 LTD, with long name MAHIM BUS STATION to BARVE NAGAR (UP). Its direction 0 starts at Mahim Bus Station. The reference uses label 321 and describes the same origin and a continuation to Barve Nagar after the airport. This is a plausible route match, but the short names differ and an exact route identifier or timetable version match has not been established.

For Friday 2026-10-16, the daily GTFS calendar activates all 57 trips on this route and direction. The GTFS input declares a service period of 2026-08-19 through 2027-02-15, but the feed download date is unknown. No calendar_dates.txt was supplied, so date-specific exceptions cannot be checked. The comparison uses first-stop departure times only and does not compare estimated intermediate times on the reference page.

## Results

| Measure | Result |
|---|---:|
| Reference departures | 33 |
| GTFS departures | 57 |
| Exact departure-time overlaps | 31 |
| Reference-only departures | 2 |
| GTFS-only departures | 26 |
| Reference departures also present in GTFS | 93.9% |
| GTFS departures also present in reference | 54.4% |

The reference-only times are 06:30 and 16:49. The comparator output lists all unmatched times under data/processed/best/qualification/schedule_comparisons/airportbus_best_321_mon_sat/.

The difference may reflect a timetable revision, route-label variant, or a mismatch between the external page and the local feed. The evidence does not distinguish among those explanations. Treat the 31 shared departures as overlap between two schedule representations, not proof that the feed is correct.

## Reproduce

With the baseline built, run python scripts/compare_best_schedule.py. The script checks whether the processed baseline hashes match the available raw files, filters active GTFS trips for the comparison date, preserves hours beyond 24:00, and writes a JSON summary plus a time-by-time CSV under the processed qualification folder. It refuses to replace a non-empty comparison folder unless --overwrite is supplied.

Run python -m unittest discover -s tests -v to run the project tests.

## Next validation gate

Obtain and archive a dated route timetable directly from BEST Prawas or BEST. First compare one route whose trips have zero scheduled duration, such as 394 AS or 397 AS, then include an ordinary route and a post-midnight trip. Record the operator route label, direction, stop sequence, effective date, capture date, source artifact checksum, and data rights. The official reference is required before treating route-level schedule values as validated.

## BEST Prawas route-map check (2026-11-23)

The user supplied two BEST Prawas map-view screenshots. The 394 AS screen shows Kannamwar Nagar No.2 and Vikhroli Bus Station (E); the 397 AS screen shows Kannamwar Nagar, Building No.124 and Vikhroli Bus Station (E). These visible terminal labels agree with the corresponding GTFS route endpoints.

| Route | GTFS directions | Trips | Stops per trip | Zero-duration trips |
|---|---:|---:|---:|---:|
| 394 AS | 2 | 600 | 8 | 600 |
| 397 AS | 2 | 668 | 11 | 668 |

Each direction has one reconstructed GTFS stop pattern. The screenshots show maps and endpoint names but no departure times or schedule effective date. They support route identity and terminal-name checks; they do not resolve the zero-duration schedules or provide a stop-by-stop validation. The GTFS feed also lacks shapes.txt, so its full road alignment cannot be compared to the app line from the supplied files.

A machine-readable transcription of the visible labels and comparison limits is in data/references/best_prawas_route_maps.json. The screenshot images themselves are not copied into the repository.

## BEST Prawas timetable and Google Maps sequence check (2026-11-23)

The user supplied two BEST Prawas timetable screenshots for route **394 AS**, from Kannamwar Nagar No.2 to Vikhroli Bus Station (E). The selected date shown is 23-Nov-2026. The screenshots show 16 departures in two partial views: 05:50, 05:57, 06:04, 06:07, 06:08, 06:11, 06:18, 06:23; and 21:49, 21:53, 22:00, 22:10, 22:20, 22:30, 22:40, 22:50. No schedule effective date is displayed, and the screenshots are not archived in the repository.

The candidate GTFS direction is BEST_2898 (direction 1), with 301 trips and eight stops per trip. Its first-stop departures range from 05:50 to 22:50. **Eleven of the 16 visible Prawas times match exactly; five visible Prawas times are absent from this GTFS direction** (05:57, 06:04, 06:11, 06:18, 21:53). The visible first and last departures agree with the GTFS extrema. Because the screenshots are partial, no GTFS-only count is reported and this does not establish a full-day timetable match.

There are three-minute gaps in the displayed list (06:04�06:07 and 06:08�06:11), but the gaps vary across both screenshots; they do not establish a fixed three-minute headway. Every candidate GTFS trip for this direction repeats one time value at all eight stops and is classified as zero-duration. The cross-check therefore concerns origin departures only; it cannot validate intermediate stop times or trip duration. The user reports that the opposite direction was unavailable in Prawas; that availability was not independently checked.

The user also transcribed a Google Maps sequence for the reverse direction under the label **397 A**: 00:11 Vikhroli Station (E), 00:13 Kinnari Hall, then one-minute increments through Janata Market at 00:19. No screenshot, URL, or observation date accompanied the transcription. The stop order from Kinnari Hall through Janata Market matches GTFS route BEST_2901 (labelled **397 AS**, direction 0) at stops 4�10. The reported origin name is only an approximate match; two Vikhroli Station Road (E) stops in the GTFS pattern are not listed, and the GTFS terminal Building No.124 comes after the final reported stop. The closest GTFS origin departure to 00:11 is 00:10, one minute earlier, but the route-label and date differences prevent treating this as an exact schedule match. The candidate GTFS trip repeats 00:10 at all 11 stops, so it cannot validate the reported progression.

| Evidence | Candidate GTFS | Result | Interpretation |
|---|---|---|---|
| 394 AS Prawas departures | BEST_2898, direction 1 | 11 of 16 visible times overlap; 5 visible times are reference-only | Partial primary-app cross-check, with timing discrepancies |
| 397 A Google Maps sequence | BEST_2901 / 397 AS, direction 0 | Kinnari Hall through Janata Market aligns with GTFS stops 4�10; first reported time is one minute later than the nearest GTFS departure | Candidate route-pattern support only; route variant and date remain unconfirmed |

The machine-readable transcription and comparison limits are in [best_route_schedule_observations_2026-11-23.json](../data/references/best_route_schedule_observations_2026-11-23.json). The primary schedule-validation gate remains open: obtain a complete dated timetable, resolve the five Prawas mismatches and the 397 A/397 AS label, and record a reproducible source artifact before treating the schedule as validated.

