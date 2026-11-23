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

The user supplied 51 BEST Prawas timetable screenshots for route 394 AS, from Kannamwar Nagar No.2 to Vikhroli Bus Station (E). The selected service date is 23-Nov-2026. A manual transcription produced 410 visible time entries across overlapping views. After deduplication, 339 distinct times appear across all origin labels; nine distinct times also appear with the alternate label “Vikhroli Station Road (E) - Vikhroli Bus Station (E).” Six of those times appear only with that alternate label and were excluded. The resulting reference file contains 333 distinct selected-origin departure times, from 05:50 through 22:50. The screenshot archive and a SHA-256 manifest are kept in the local workspace; the image files are not tracked in GitHub.

The consecutive gaps between the 333 visible departure times range from 1 to 10 minutes, with a median of 3 minutes. This supports a 3-minute median interval, not a fixed 3-minute headway. The page views overlap and some edges are clipped, so completeness of the full-day timetable is not established.

The candidate GTFS direction is BEST_2898 (direction 1), with 301 distinct first-stop departures and eight stops per trip. 220 of 333 distinct Prawas times overlap exactly with GTFS (66.1% of visible Prawas times; 73.1% of GTFS times). There are 113 selected-origin times not in the candidate GTFS, and 81 candidate GTFS times not seen in the supplied screenshots. The latter are not classified as schedule mismatches because screenshot coverage is not certified complete. The visible 05:50 and 22:50 bounds agree with the GTFS extrema. Every candidate trip repeats one time value at all eight stops and is classified as zero-duration, so this comparison concerns first-stop departures only.

Nine distinct timestamps also appear with the alternate origin label. For 12:39, 14:20, and 16:36, a selected-origin row appears at the same minute and remains in the comparison. Times 12:13, 13:17, 13:38, 14:38, 15:24, and 15:41 appear only with the alternate label and are excluded. This origin-label filtering is documented in the machine-readable metadata and reference CSV.

The user reports that the opposite 394 AS direction was unavailable in Prawas; this was not independently verified. The supplied timetable screenshots cover only Kannamwar Nagar No.2 to Vikhroli Bus Station (E).

A newly supplied Google Maps itinerary displays route A-397, service by BEST, from Vikhroli Bus Station (E), stop ID 14227. The visible stop list proceeds through two Vikhroli Station Road (E) stops, Kinnari Hall, Kannamwar Nagar No.1, Kannamwar Nagar Hospital, Buildings No.150, No.175, and No.188, to Janata Market at 00:19. These stops match the first ten ordered stops of candidate GTFS route BEST_2901 (397 AS, direction 0), including the origin stop ID. The itinerary labels the bus route destination/headsign “Kannamwar Nagar or Building No.124,” but its explicit transit stop list ends at Janata Market; it does not show a stop-level 00:20 arrival at Building No.124. This is strong stop-pattern support for the candidate, while the displayed route label A-397 differs from 397 AS.

The Google Maps header shows 12:11 AM (Monday) to 12:20 AM (9 minutes), and the bus leg shows 8 minutes (9 stops). The calendar date is not displayed, so the schedule period is unknown. Candidate GTFS has a 00:10 origin departure, one minute earlier than the itinerary's 00:11 origin. Its 00:10 trip repeats that value at all 11 stops, so the intermediate times cannot validate the GTFS. Treat the Google Maps screen as route-planning evidence, not a dated BEST timetable or observed running-time record.

| Evidence | Candidate GTFS | Result | Interpretation |
|---|---|---|---|
| 394 AS Prawas selected-origin times | BEST_2898, direction 1 | 220/333 distinct Prawas times overlap; 113 are absent from GTFS and 81 GTFS times are not seen in screenshots | Broad primary-app screenshot comparison; completeness and effective date unresolved |
| A-397 Google Maps itinerary | BEST_2901 / 397 AS, direction 0 | Origin stop ID 14227 and the first ten ordered stops align through Janata Market | Strong stop-pattern candidate match; exact route identity and service date unresolved |

The Prawas departure CSV and source metadata are in [best_prawas_394_as_2026-11-23.csv](../data/references/best_prawas_394_as_2026-11-23.csv) and [best_prawas_394_as_2026-11-23.json](../data/references/best_prawas_394_as_2026-11-23.json). The combined evidence record is [best_route_schedule_observations_2026-11-23.json](../data/references/best_route_schedule_observations_2026-11-23.json). Regenerate the local first-stop comparison with:

    python scripts/compare_best_schedule.py --reference-csv data/references/best_prawas_394_as_2026-11-23.csv --metadata data/references/best_prawas_394_as_2026-11-23.json --output-dir data/processed/best/qualification/schedule_comparisons/best_prawas_394_as_2026-11-23

Before schedule values inform optimization, confirm screenshot completeness and timetable effective date with BEST/Prawas, investigate observed time differences against an exact feed version, and obtain demand and observed running-time data separately.

