# NYC Yankee Stadium Driver-Cycle Benchmark

## Question

How does including approach and passenger-pickup waiting time change the apparent economics of event-area rideshare trips?

## Design

Three April 14-16, 2025 Yankees home games are paired by weekday with April 7-9 controls. Each phase is aligned to the 7:05 p.m. home-game start. West Concourse is the stadium core; the comparison ring contains official TLC taxi zones within one mile of the core polygon. NYC is a regulated-market measurement benchmark, not a proxy for Nashville or Chicago.

Approach time is request to driver arrival, pickup wait is arrival to passenger pickup, and occupied time is pickup to drop-off. Full-cycle pay per hour divides reported driver pay by request-to-drop-off time. It is gross trip-level compensation, not net hourly earnings or a complete shift-level wage.

## Matched results

Values are medians of three weekday-matched event/control percentage changes. Overhead is reported as a percentage-point change.

| Zone | Phase | Volume | Approach time | Pickup wait | Occupied pay/hour | Full-cycle pay/hour | Overhead share |
|---|---|---:|---:|---:|---:|---:|---:|
| core | pregame_2h | 1.5% | 1.8% | 13.2% | 2.1% | 0.1% | -0.8% pts |
| core | game_first_2h | 18.8% | 16.3% | -23.7% | 7.7% | 8.6% | -0.5% pts |
| core | game_late_post_2h | 162.9% | 97.0% | -37.2% | 24.6% | 21.4% | -0.2% pts |
| one_mile_ring | pregame_2h | -2.8% | -4.0% | -2.3% | 1.8% | 0.7% | -1.0% pts |
| one_mile_ring | game_first_2h | 2.6% | -1.2% | 2.0% | 1.1% | 2.1% | -0.2% pts |
| one_mile_ring | game_late_post_2h | 9.5% | 17.4% | -9.4% | 0.5% | -1.6% | 1.4% pts |

## What the complete clock changes

The clearest reversal appears in the one-mile ring during the late-game/postgame phase. Occupied-only driver pay per hour was 0.5% above its matched controls, but approach time increased 17.4%; full request-to-drop-off pay per hour consequently fell 1.6%. An occupied-trip metric alone would give the wrong directional answer for this slice.

Pregame in the stadium core shows a milder version of the same issue. Occupied pay per hour increased 2.1%, while full-cycle pay per hour was nearly unchanged at 0.1% after pickup waiting increased 13.2%.

The core late-game/postgame result is different: trip volume increased 162.9% and full-cycle pay per hour increased 21.4% even though approach time nearly doubled. In this phase, stronger reported trip pay and longer occupied trips were large enough to offset the observed pre-pickup burden. The analytical lesson is therefore not that event cores or adjacent zones are universally better; it is that the recommendation can change when the full driver clock is measured.

## Interpretation boundary

Only three event dates are available in this bounded pilot, so these are descriptive paired estimates rather than a citywide causal effect. Taxi zones are coarse, event attendance is not observed, and request time does not include time spent logged in before receiving a request. Platform-reported driver pay excludes vehicle expenses and may reflect NYC-specific pay rules. The hourly figures describe time inside completed trip cycles, not all online time, and must not be presented as shift-level earnings.

The comparison deliberately ends four hours after first pitch because the retained source slice ends at midnight; no incomplete extended-postgame phase is reported.

## QA

- Raw bounded trips: 157,368
- Trips in the three analysis phases: 104,692
- Excluded for impossible or extreme timing/pay/distance values: 311
- Usable trips: 104,381
- Usable platform records: HV0003=77,203, HV0005=27,178
