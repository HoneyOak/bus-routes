# Curated timetable references

This folder contains attributed, manually transcribed schedule evidence used for cross-source checks. Per-source metadata records route, direction, displayed date, effective-date status, method, and limitations. Reference files do not replace the immutable GTFS inputs in data/raw/, and time overlap does not establish operator approval or feed accuracy.

- 321 LTD secondary reference (best_321_mon_sat.csv) is a partial extract attributed to a BEST schedule carried by Chalo, as described by airportbus.in.
- 394 AS Prawas departure extract (best_prawas_394_as_2026-11-23.csv) contains 333 distinct selected-origin times transcribed from 51 user-supplied screenshots. See its metadata (best_prawas_394_as_2026-11-23.json) and the combined route observation record (best_route_schedule_observations_2026-11-23.json).
- Prawas route-map observations (best_prawas_route_maps.json) record displayed endpoint labels for 394 AS and 397 AS.
- The user-supplied Google Maps screenshot for A-397 is transcribed in the combined observation record. Its origin stop ID and first ten listed GTFS stops align with candidate route BEST_2901 (397 AS, direction 0); the displayed label and calendar date remain unresolved.

The Prawas and Google Maps screenshot originals are preserved in source_artifacts/ in the local workspace with a SHA-256 manifest. They are excluded from GitHub because the repository stores curated text evidence, not attached UI screenshots. No source screenshot is edited. The timetable effective date, full-day completeness, exact upstream GTFS version, and license scope remain unresolved.

