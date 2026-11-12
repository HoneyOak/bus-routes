# Research data handling

This directory is part of the reproducible GTFS baseline. Raw files and generated data are excluded from Git by research/.gitignore.

Place an authorized snapshot's seven text files in data/raw/: agency.txt, calendar.txt, feed_info.txt, routes.txt, stop_times.txt, stops.txt, and trips.txt. Do not replace or edit the source files in place.

The current local snapshot names BLRTransit as publisher and spans 2026-08-19 through 2027-02-15. It is a multi-operator MMR feed, not an official BEST-only publication. Record source URL, retrieval date, service dates, license, and checksum before using a new snapshot.

Generated normalized files and BEST outputs belong under data/processed/. See data/source_registry.json and docs/data_provenance.md for the current source assessment.
