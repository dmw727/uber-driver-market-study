# Chicago Source Pilot Log

## Status

Feasibility validation completed; analytical extraction is not yet production-ready.

## Confirmed

- The preferred official source is the year-specific City of Chicago dataset `8bbv-3wbe`, not the slower combined 2025-present view `6dvr-xwnh`.
- The 2026 partition currently covers January 1 through August 31, 2026.
- All required trip, time, fare, distance, and community-area fields are present.
- Small unfiltered samples return promptly and can be reproduced with `scripts/validate_chicago_source.py`.
- August 2026 provides a useful Monday design: home games on August 3, 17, and 31, with away-team Mondays on August 10 and 24 as candidate controls.

## Data-quality observations

- Trip timestamps are rounded to 15-minute intervals, so windows must align to those bins.
- Zero-dollar records occur and require a documented inclusion rule.
- `percent_distance_chicago` can be slightly greater than 1, so percentage-range checks need a tolerance or exclusion rule.
- Fare is passenger spending, not driver pay or net earnings.
- Community Area 6 covers Lake View and is broader than the immediate Wrigley Field environment.

## Access constraint discovered

The combined view timed out on bounded requests. The year-specific view supports metadata and small samples, but unauthenticated server-side aggregates and multi-hour filtered extraction also exceeded practical timeouts during this pass. No event-effect estimates should be reported from incomplete queries.

## Production gate

Before resuming event analysis, establish one of these reproducible extraction paths:

1. A documented monthly or date-partitioned bulk export from the official portal.
2. An authenticated Socrata query path tested against one eight-hour window.
3. A smaller official historical partition that supports the same event/control design without timeouts.

The chosen path must save the extraction query or filter, source update timestamp, row count, and file checksum. Only then should the pilot expand to three or more home events and at least three screened control dates per event.

## Interpretation

This is a productive pilot result, not a failed analysis. It identified schema quirks, source revisions, geographic limitations, and an extraction bottleneck before those issues could become invisible weaknesses in a polished portfolio claim.
