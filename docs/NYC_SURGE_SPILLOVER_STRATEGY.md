# NYC Surge-Spillover Strategy Test

## Strategy question

Can a driver capture event-associated compensation in the venue spillover area while choosing trips that move away from stadium traffic, thereby preserving more trip-completion capacity during the two-hour pregame window?

## Design

The April 14-16, 2025 Yankees home-game pregame windows are compared with nine Monday-Wednesday evenings when the Yankees were away. Normal passenger-fare and driver-pay models are trained only on controls and adjust for platform, pickup zone, weekday, 15-minute slot, miles, occupied time, approach time, pickup waiting, and trip-direction class. Each implied premium is the event actual-to-model ratio relative to the corresponding control ratio; neither is a platform-reported surge multiplier.

Spillover-away trips begin in the one-mile ring, end outside the ring, and finish at least one-quarter mile farther from Yankee Stadium than the pickup-zone centroid. Stadium-bound trips begin in the ring and end in the stadium core.

## Results

| Strategy | Event trips | Volume change | Passenger-fare premium | Driver-pay premium | Cycle change | Event cycles / 2h | Gross capacity proxy / 2h |
|---|---:|---:|---:|---:|---:|---:|---:|
| stadium_bound | 289 | 44.5% | -3.9% | 0.2% | 8.1% | 6.49 | $76.12 |
| spillover_local | 3191 | -1.7% | -4.2% | -0.4% | -4.0% | 7.54 | $76.89 |
| spillover_away | 2301 | -5.0% | -2.8% | 0.0% | -7.2% | 5.03 | $98.10 |
| core_departure | 284 | -8.4% | -4.9% | -0.3% | 5.6% | 6.06 | $79.76 |

## Interpretation boundary

The fare and pay premiums are model-implied and event-associated; they do not reveal the app's surge multiplier. NYC's TLC minimum per-trip payment standard, based partly on time and mileage, can compress variation in reported driver pay. A near-zero driver-pay premium therefore cannot establish how the same strategy would perform in Nashville. Passenger base fare and reported driver pay are separate outcomes and should not be treated as interchangeable. Taxi-zone centroids approximate direction and do not reveal the exact route. Cycle capacity assumes back-to-back comparable completed trips and excludes idle time before the next request, repositioning after drop-off, expenses, cancellations, and the possibility that an away trip leaves the premium area. It is a throughput ceiling, not observed rides per driver.

Control dates were screened for Yankees home games, not every possible local event or source of chaotic demand. Date-level control residuals in the companion CSV should be reviewed before treating the baseline as ordinary.

## QA

- Raw pregame trips: 77,099
- Excluded invalid timing/pay/distance records: 381
- Classified strategy trips: 73,787
- Other directional patterns not used: 2,931
- Normal-pay training trips: 55,442
- Control-model R-squared (log driver pay): 0.961
- Control-model R-squared (log passenger base fare): 0.847
