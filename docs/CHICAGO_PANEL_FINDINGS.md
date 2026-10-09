# Chicago Monday Panel: Preliminary Findings

## Answer first

Across all 22 published Mondays, Wrigley home-game dates averaged 9,716 area-touching trips versus 6,541 on comparison Mondays, a descriptive difference of 48.5%. The direction and approximate magnitude remain stable across the planned sensitivity exclusions.

## Sensitivity estimates

| Scenario | Dates (event/control) | Relative difference | Date-bootstrap 95% interval |
|---|---:|---:|---:|
| All published Mondays | 22 (9/13) | 48.5% | 39.2% to 58.5% |
| Non-weather-stress Mondays | 15 (8/7) | 45.9% | 31.5% to 62.2% |
| Non-weather and non-holiday Mondays | 13 (8/5) | 55.2% | 42.0% to 71.4% |
| Exclude Aug 31 volume anomaly date | 21 (8/13) | 50.0% | 40.9% to 60.0% |

## Adjusted estimate

A compact log-volume regression adjusting for weather stress, mean evening temperature, and week-of-season estimates a 44.8% event-date difference (HC1 robust 95% interval: 32.0% to 58.8%).

## Interpretation limits

This is a bounded observational estimate for trips touching Community Area 6, not a causal estimate of all rideshare demand or driver earnings. The public data do not report drivers online, unfulfilled requests, dynamic pricing, or rider intent. Weather is modeled from hourly reanalysis at Wrigley coordinates, and competing-event classification remains incomplete. August 31 is retained only in the volume sensitivity analysis; its monetary fields are unusable.

The result is nevertheless strong enough to guide the next stage: inspect event-time arrival and departure shapes, complete competing-event labels, and test whether event dates increase occupied-vehicle pressure rather than merely shifting trip timing.
