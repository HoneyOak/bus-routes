# Data source and provenance review

Review date: 2026-11-12

This report covers a snapshot preserved in the companion research workspace. The raw GTFS files, audit ZIP, and generated tables are not committed in this repository. The archive checksum identifies the local audit package only.

## Decision

Keep the supplied feed as an exploratory BEST baseline. Its local metadata declares BLRTransit as publisher and service dates 2026-08-19 through 2027-02-15. A public Mobility Database record points to a community GTFS repository and reports the same service window. This is a strong source-family lead, but the exact uploaded GTFS variant and its upstream archive checksum have not been matched. The feed remains unverified as an official or complete BEST schedule.

## Evidence

### Supplied snapshot

The preserved package is mumbai-gtfs-audit-package.zip (SHA-256 8dd9baa02963f9fbf38725d1e3944a80a56b2792d8cad7fc6708700b92a4a9f4, 27,260,240 bytes). It contains the seven raw GTFS text files under data/raw/, along with the audit and normalized outputs. The feed declares:

- Publisher: BLRTransit (https://blrtransit.com)
- Service range: 2026-08-19 to 2027-02-15
- Agencies: BEST, TMT, KDMT, and VVMT
- Routes: 1,609 across the feed; 937 BEST route IDs

The raw files do not identify a retrieval timestamp, source archive URL, archive version, or data license. The feed service range is not a download date or evidence that the listed schedules were operated.

### Likely source family

The Mobility Database community-feed record [mdb-3138](https://mobilitydatabase.org/feeds/gtfs/mdb-3138) lists the producer URL as https://github.com/croyla/mumbai-gtfs/raw/refs/heads/main/gtfs_compat.zip. Its history reports a version fetched on 2026-08-20 with the exact same 2026-08-19 to 2027-02-15 service range as the local feed.

The linked [croyla/mumbai-gtfs repository](https://github.com/croyla/mumbai-gtfs) describes two variants: gtfs.zip preserves original route variants, while gtfs_compat.zip merges routes for compatibility. The local raw files have 1,609 route IDs, while Mobility Database reports 935 routes for its compatibility-feed record. That difference is consistent with the repository's description of the two formats, but it does not establish that the local files came from gtfs.zip. The repository README describes KDMT, TMT, and BEST; the local raw feed also contains VVMT.

No upstream ZIP matching the local raw files, archived version checksum, or file-by-file comparison was available in the supplied package. The local package checksum above identifies the audit package, not the upstream GTFS archive.

### License scope

GitHub labels the repository license MIT-0 and its [LICENSE file](https://github.com/croyla/mumbai-gtfs/blob/main/LICENSE) contains a broad permission grant for the defined “Software.” The supplied raw snapshot has no separate license or attribution file. The source-family evidence is not enough to confirm that this repository license covers the exact uploaded files or resolves rights in underlying operator schedule data. Record the repository license as a lead, not as confirmed license metadata for this snapshot.

### Independent BEST references

BEST's official [Bandra Kurla Complex routes PDF](https://www.bestundertaking.com/assets/pdf/mmrconnect.pdf) lists schedules and itineraries for BKC-10 through BKC-13 and BKC-21 through BKC-25. None of those labels exactly match a BEST route_short_name in the supplied feed, and no effective date was identified in the document text reviewed. It is a narrow reference, not a validation of this snapshot.

The official MCGM [Year Book 2025](https://www.mcgm.gov.in/irj/go/km/docs/documents/HomePage%20Data/Whats%20New/English%20Year%20Book%202025%20Portal.pdf) reports 427 BEST routes as of 2025-03-31. That count is not directly comparable to the local feed's 937 BEST route IDs: the dates and counting units differ, and the community repository describes route variants that can be split or merged. Treat it as a reason to reconcile route IDs and public route labels, not as evidence that either count is wrong.

The [BEST Prawas app listing](https://play.google.com/store/apps/details?id=com.dimts.best.bestapplication) says the BEST Undertaking's app includes a static timetable for each route. It is a promising official schedule reference for a later manual comparison, but this review did not inspect an app timetable or archive a dated schedule from it.

## What is established

- The raw snapshot is multi-operator MMR data with BEST records, not a BEST-only source feed.
- Its feed metadata names BLRTransit and declares the dates above.
- A community-feed record points to the Mumbai GTFS repository and has a matching service window.
- The exact upstream file/version, exact byte identity, retrieval date, and license applicability remain unconfirmed.
- The reviewed official BEST PDF does not overlap the feed's route labels, so independent schedule validation is still pending.

## Next research gate

Use a dated BEST Prawas timetable or a schedule export supplied by BEST to compare a small, reproducible sample of routes with the local BEST records. Begin with routes flagged for zero-duration schedule values, and include ordinary routes and post-midnight trips. For each sample, save the reference date and route label, compare ordered stops and scheduled times, and record whether the match is exact, partial, or unavailable. Do not treat a community validator result or a route-count match as proof of operator approval.

In parallel, retain the Mobility Database archive date and source URL as candidate provenance, and obtain the exact source archive/hash and applicable data license before publishing or redistributing the raw schedules.
