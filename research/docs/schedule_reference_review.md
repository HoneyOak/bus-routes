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

