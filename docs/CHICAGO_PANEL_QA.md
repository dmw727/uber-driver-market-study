# Chicago Monday Panel: Data-Quality Review

## Coverage

The panel contains 22 published Mondays: 9 Cubs home-game dates and 13 comparison dates. The source had not yet published 3 configured September dates when the extract ran.

Unavailable dates: 2026-09-07, 2026-09-14, 2026-09-21.

## Date-level checks

| Date | Group | Unique trips | Zero fares | Missing fares | Duplicate IDs |
|---|---|---:|---:|---:|---:|
| 2026-04-06 | control | 7,132 | 10 (0.14%) | 8 | 0 |
| 2026-04-13 | control | 6,328 | 17 (0.27%) | 4 | 0 |
| 2026-04-20 | event | 9,329 | 42 (0.45%) | 13 | 0 |
| 2026-04-27 | control | 6,709 | 36 (0.54%) | 3 | 0 |
| 2026-05-04 | event | 10,013 | 19 (0.19%) | 31 | 0 |
| 2026-05-11 | control | 6,403 | 15 (0.23%) | 1 | 0 |
| 2026-05-18 | event | 10,355 | 15 (0.14%) | 8 | 0 |
| 2026-05-25 | control | 8,203 | 9 (0.11%) | 3 | 0 |
| 2026-06-01 | control | 6,375 | 11 (0.17%) | 131 | 0 |
| 2026-06-08 | control | 6,653 | 13 (0.20%) | 3 | 0 |
| 2026-06-15 | event | 9,366 | 9 (0.10%) | 6 | 0 |
| 2026-06-22 | control | 6,081 | 6 (0.10%) | 0 | 0 |
| 2026-06-29 | event | 9,958 | 7 (0.07%) | 0 | 0 |
| 2026-07-06 | control | 7,059 | 14 (0.20%) | 1 | 0 |
| 2026-07-13 | control | 6,939 | 23 (0.33%) | 5 | 0 |
| 2026-07-20 | event | 9,618 | 25 (0.26%) | 4 | 0 |
| 2026-07-27 | control | 5,958 | 10 (0.17%) | 2 | 0 |
| 2026-08-03 | event | 9,672 | 31 (0.32%) | 5 | 0 |
| 2026-08-10 | control | 5,998 | 29 (0.48%) | 1 | 0 |
| 2026-08-17 | event | 10,190 | 39 (0.38%) | 8 | 0 |
| 2026-08-24 | control | 5,195 | 40 (0.77%) | 4 | 0 |
| 2026-08-31 | event | 8,944 | 864 (9.66%) | 3 | 0 |

## Distribution check

Median event volume is 9,672 trips versus 6,403 for comparison Mondays. Event-date volume ranges from 8,944 to 10,355; comparison volume ranges from 5,195 to 8,203.

Across the panel there are 0 duplicate trip IDs and 0 rows that fail the Community Area 6 filter check.

Dates with a zero-fare rate of at least 2%: 2026-08-31 (9.66%).

## Decision

The panel is ready for covariate enrichment and descriptive modeling, but not yet for a causal claim. Weather, holiday, and competing-event labels must be attached before adjusted comparisons. August 31 monetary outcomes remain excluded because of the confirmed all-zero charge anomaly; its trip counts remain available for volume sensitivity analysis.
