# Chicago Monday Pilot: Data-Quality Review

## Dataset and grain

Each cached row is one public Chicago TNP trip touching Community Area 6 as a pickup, drop-off, or both during 4:00-11:59 PM local time. The expanded pilot contains three Cubs home-game Mondays and four candidate-control Mondays.

## Core checks

| Date | Group | Unique trips | Duplicate IDs | Missing fares | Zero fares | Neither-area rows |
|---|---|---:|---:|---:|---:|---:|
| 2026-07-06 | control | 7,059 | 0 | 1 | 14 (0.20%) | 0 |
| 2026-07-27 | control | 5,958 | 0 | 2 | 10 (0.17%) | 0 |
| 2026-08-03 | event | 9,672 | 0 | 5 | 31 (0.32%) | 0 |
| 2026-08-10 | control | 5,998 | 0 | 1 | 29 (0.48%) | 0 |
| 2026-08-17 | event | 10,190 | 0 | 8 | 39 (0.38%) | 0 |
| 2026-08-24 | control | 5,195 | 0 | 4 | 40 (0.77%) | 0 |
| 2026-08-31 | event | 8,944 | 0 | 3 | 864 (9.66%) | 0 |

Median event-date volume was 9,672 trips versus 5,978 for controls, an unadjusted difference of 61.8%. This is descriptive and precedes control screening and uncertainty estimation.

Pickup and drop-off counts overlap when a trip begins and ends inside Community Area 6. Unique-area volume therefore uses pickup + drop-off - both, rather than adding directional counts directly.

## Event timing check

Highest-volume event-date 15-minute bins:

| Date | Time | Pickups | Drop-offs |
|---|---|---:|---:|
| 2026-08-31 | 17:30 | 152 | 367 |
| 2026-08-17 | 18:00 | 113 | 395 |
| 2026-08-17 | 18:15 | 111 | 385 |
| 2026-08-17 | 17:45 | 107 | 386 |
| 2026-08-31 | 18:00 | 135 | 341 |
| 2026-08-03 | 22:15 | 353 | 121 |
| 2026-08-31 | 17:45 | 135 | 338 |
| 2026-08-03 | 18:00 | 131 | 333 |
| 2026-08-31 | 17:15 | 155 | 299 |
| 2026-08-03 | 18:15 | 145 | 297 |

The time profile is a plausibility check, not causal evidence. A credible event pattern should show elevated arrivals before the scheduled start and elevated departures later in the evening.

## Control-period fare screening

Highest control-date median-fare bins with at least 30 trips:

| Date | Time | Trips | Median fare | P90 fare | Median fare/mile | Median fare/minute |
|---|---|---:|---:|---:|---:|---:|
| 2026-07-27 | 17:00 | 219 | $15.00 | $40.00 | $4.48 | $0.84 |
| 2026-07-27 | 17:15 | 227 | $15.00 | $32.50 | $4.49 | $0.85 |
| 2026-07-27 | 17:30 | 210 | $15.00 | $37.50 | $3.46 | $0.73 |
| 2026-07-27 | 16:45 | 160 | $13.75 | $27.50 | $3.15 | $0.60 |
| 2026-07-06 | 16:00 | 185 | $12.50 | $32.50 | $2.59 | $0.63 |

Fare spikes must be checked against trip distance and duration, competing events, weather, and road disruptions. Candidate controls with unexplained anomalies will be rejected or analyzed as secondary event periods.

## Readiness decision

**Suitable for expanded exploratory work; not yet suitable for a causal portfolio claim.** The date sample is now adequate for screening consistency, but weather, competing events, road conditions, and the August 31 zero-fare anomaly still require resolution.

Three candidate controls are excluded from the clean primary baseline. July 27 had confirmed severe thunderstorms and flooding, August 10 had confirmed storm activity, and July 6 immediately followed the July 4 holiday/severe-weather period and a Cubs home series. They remain useful as weather-stress or holiday-recovery sensitivity observations. August 24 qualifies as the first clean control: the Cubs were away, no precipitation was recorded, and the National Weather Service reported no significant weather.

The August 31 zero-fare pattern is analytically distinct from high demand. Chaotic demand can produce higher trip counts, longer durations, and higher fares, but it does not directly explain a sharp increase in exact zeroes. A focused charge-detail extraction found:

| August 31 charge check | Trips |
|---|---:|
| All area-matching trips | 8,944 |
| Zero-fare trips | 864 |
| Zero fare and zero trip total | 792 |
| Zero fare but positive trip total | 72 |

The 792 all-zero-charge records still contain plausible positive distance and duration: their median trip was 4.2 miles and 15.2 minutes. They become frequent from approximately 6:30 PM through the postgame period. No field identifies these as free, promotional, or cancelled rides. Accordingly, the evidence supports a **monetary-data anomaly**, not a free-ride conclusion. These records remain valid enough for bounded trip-volume counts but must be excluded from fare, revenue, and price-pressure calculations. The timing overlap also means August 31 volume estimates should receive a sensitivity check for source or provider composition if a suitable field becomes available.

## Expansion decision

The pilot shows that selecting a handful of apparently ordinary Mondays creates fragile controls: weather, holidays, and unrelated events can dominate a single date. The production sample should therefore expand to a season-wide Monday panel rather than searching for a few supposedly perfect replacements. The official MLB schedule feed produced a manifest of 25 Mondays from April 6 through September 21: 10 Wrigley home-game Mondays and 15 non-home Mondays.

Each Monday will receive mutually exclusive analytical labels for Wrigley event status, weather stress, holiday adjacency, and known competing demand shocks. The primary estimate will compare Wrigley-event Mondays with ordinary Mondays while controlling for time and weather; weather-stress and holiday-recovery Mondays will remain as explicit subsets. This increases the date-level sample, exposes chaotic non-baseball demand, and avoids selecting controls based on the outcome after seeing it.

Next: build the full Monday date manifest, download the remaining bounded evening extracts, and attach weather/event covariates before estimating effects and uncertainty. Exclude August 31's affected records from monetary outcomes while retaining them for volume sensitivity analysis.
