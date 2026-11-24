# Preliminary BEST timetable cross-check

Review date: 2026-11-12

## Decision

The route 321 comparison is a partial secondary-source check. It is useful as a reproducible warning that the supplied GTFS and the schedule copy do not agree exactly. It does not validate the GTFS as an official, complete, or accurate BEST feed. Keep the current feed exploratory.

## Reference and limitations

The reviewed airportbus.in page labels the service 321 from Mahim Bus Station to CSMIA Terminal 2 and says the route continues to Barve Nagar. Its data-source page says the displayed Mumbai departures are BEST schedules carried by Chalo, retrieved 2026-10-16. It also says only the first stop is timetabled on the route page; intermediate times are estimated. airportbus.in states that it is not affiliated with BEST or the airport.

The BEST Prawas app listing identifies BEST Undertaking as the app developer and describes a static timetable for each route. The user later supplied dated Prawas timetable screenshots for route 394 AS; those are primary app-screen evidence, though the schedule effective date and completeness remain unknown.

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

## Next validation gate (updated 2026-11-24)

BEST Prawas is now the selected primary timetable reference, but the current screenshots do not establish a complete service day or timetable effective date. Obtain a complete operator-sourced timetable export, or a complete Prawas timetable capture with its effective date and service-day rules. Record the operator route label, direction, stop sequence, effective date, capture date, source artifact checksum, and data rights. Include a route with positive scheduled durations and a post-midnight trip before treating route-level timing as validated.
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



## Feed source selection and effectiveness decision (2026-11-24)

### Selected reference source

The selected primary source for schedule checks is the BEST Prawas app. Its Google Play listing displays developer name THE BEST, describes the app as developed by BEST Undertaking, and lists a static timetable for each route ([BEST Prawas listing](https://play.google.com/store/apps/details?id=com.dimts.best.bestapplication)). That supports treating the app as the primary operator timetable reference. It is an app interface, not a publicly downloadable GTFS archive. The source search did not identify a public BEST-issued GTFS download.

### Candidate GTFS status and service-date check

The available GTFS remains the local exploratory BLRTransit snapshot. The corresponding Mobility Database record labels the feed “Community Feed,” links to a community repository, and records its latest fetch as 2026-08-20 with a declared service period of 2026-08-19 through 2027-02-15 ([Mobility Database record](https://mobilitydatabase.org/feeds/gtfs/mdb-3138), [producer repository](https://github.com/croyla/mumbai-gtfs)). The local `calendar.txt` includes service on all seven days through 2027-02-15, so the selected Prawas service date, Monday 2026-11-23, is covered by the declared calendar. This is a calendar-range check only: `calendar_dates.txt` is missing, and the exact local archive has not been matched to the upstream version.

### 394 AS departure comparison

For Kannamwar Nagar No.2 to Vikhroli Bus Station (E), the supplied Prawas screenshots show 333 distinct selected-origin departures on the selected date. Candidate GTFS route BEST_2898, direction 1, has 301 distinct departures. Exactly 220 times overlap: 66.1% of departures visible in Prawas and 73.1% of candidate GTFS departures are represented in the screenshots. The 113 Prawas times absent from GTFS are concrete discrepancies, subject to transcription and route-mapping limits. The 81 GTFS times not shown in the screenshots are not classified as errors because screenshot completeness is unproven. All 301 candidate trips repeat the same timestamp at all eight stops, producing zero scheduled duration; those values cannot supply running times.

### 397 A route-pattern check

The Google Maps screenshot for A-397 shows 00:11 from Vikhroli Bus Station (E) and the same first ten stop names/order as candidate BEST_2901 / 397 AS direction 0 through Janata Market. GTFS has a 00:10 departure for that candidate trip, and the screenshot's bus leg is shown as eight minutes. Since the candidate repeats one time across all 11 stops and the screenshot does not display a calendar date, this is stop-pattern support only, not a validation of schedule accuracy or actual running time.

### Decision

The current GTFS is not suitable for schedule-based operational optimization: its exact upstream snapshot is unresolved, the 394 AS check has substantial unmatched primary-app departures, and its sampled stop times encode no usable travel duration. Keep it for exploratory route-pattern mapping. The Prawas screenshots establish a useful operator-source baseline for the observed direction, but not a complete or versioned network timetable. Passenger demand, observed running times, capacity, costs, and equity impacts still require separate evidence before evaluating an optimization proposal.
