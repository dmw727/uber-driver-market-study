# Chicago Local Supply-Pressure Subset Analysis

## Question

How did the balance between observed ride demand and engaged driver capacity change around Wrigley Field events, even though public data does not report drivers logged into an app?

This analysis will estimate local service pressure and bounds. It will not claim to recover the exact number of online drivers.

## Unit of analysis

One observation will be a 15-minute interval for one study geography and date.

The initial geography is Community Area 6. A later sensitivity check should use nearby census tracts if privacy suppression still leaves adequate counts.

## Directly observed measures

- Pickups and drop-offs
- Unique trips touching the area
- Median and 90th-percentile fare
- Median fare per mile and fare per occupied minute
- Median trip distance and duration
- Occupied vehicle-minutes associated with trips touching the area
- Pickup/drop-off imbalance

## Engaged-driver lower bound

Every trip in progress requires at least one engaged driver. Trip start time and duration can therefore be used to estimate occupied vehicle equivalents in each interval.

For interval t:

`engaged_vehicle_equivalents_t = occupied_vehicle_minutes_t / 15`

This is a lower bound on online supply because it excludes drivers who were waiting, repositioning, or traveling to a pickup. It is also an area-associated measure rather than a precise vehicle location because public records expose trip endpoints, not routes.

Because timestamps are rounded to 15 minutes, calculate bounds under three timing assumptions:

1. Trips begin at the start of their reported bin.
2. Trips begin at the midpoint of their reported bin.
3. Trips begin at the end of their reported bin.

The resulting range communicates timestamp uncertainty instead of hiding it.

## Supply-pressure indicators

No single proxy should carry the conclusion. Report a panel containing:

- Trips per engaged vehicle equivalent
- Pickups per engaged vehicle equivalent
- Median fare per mile
- Median fare per occupied minute
- P90 fare
- Median duration and distance
- Pickup/drop-off imbalance

A period is more consistent with local supply pressure when trip volume and normalized fares rise together without the result being explained only by longer trips. Divergent indicators should be reported rather than forced into one narrative.

An optional composite index may standardize the indicators using control-period medians and median absolute deviations. The component measures must remain visible, and the index should be labeled descriptive rather than a count of drivers.

## Event-study design

Use multiple event and candidate-control Mondays. Estimate interval outcomes with:

`outcome = event_date + event_window + time_of_day + date_effects + error`

Preferred implementation:

- Count outcomes: negative-binomial regression, with Poisson used only if dispersion is acceptable
- Continuous outcomes: median or quantile regression where practical; otherwise robust date-level summaries
- Standard errors: clustered by date
- Primary windows: pregame arrival, in-game, and expected postgame departure
- Baseline: matched non-event Mondays using the same clock times and geography

With only three event dates, emphasize effect sizes, date-level variation, and confidence intervals rather than p-values. The small number of event clusters limits formal inference.

## Spatial control

Add one or more comparison community areas with similar ordinary Monday trip patterns but no simultaneous target event. A difference-in-differences comparison can then separate Wrigley-area changes from citywide Monday shocks:

`effect = (Lake View event - Lake View control) - (comparison area event - comparison area control)`

Comparison areas must be selected using pre-event behavior and urban form, not whichever area produces the preferred result.

## Monthly driver context

Use the Chicago TNP Drivers dataset only for:

- Citywide active driver-month counts
- Citywide trips per active driver
- Month-to-month changes in the broad driver pool

Do not allocate monthly drivers to Community Area 6 as though home ZIP represented work location.

## Scenario range for online supply

If a decision-oriented estimate is useful, convert engaged vehicle equivalents into an explicitly assumption-based range:

`estimated_online_drivers = engaged_vehicle_equivalents / assumed_utilization`

Report several utilization scenarios, such as 40%, 60%, and 80%, rather than selecting one undocumented rate. These scenarios are not measurements. External city utilization rates may inform the range but should not be treated as Chicago calibration without evidence.

## Control-period anomaly screening

Before accepting a control date, screen each interval for:

- Fare and fare-per-mile spikes
- Abnormal trip volume
- Weather disruption
- Road closures or transit disruption
- Concerts, festivals, or other nearby events
- Unusual trip-distance or duration mix

Controls with unexplained anomalies should be rejected, modeled separately, or retained only in a sensitivity analysis.

## Minimum defensible output

The subset analysis is ready for portfolio use when it contains:

1. At least three event dates and at least three screened controls
2. Fifteen-minute observed metrics and engaged-vehicle bounds
3. Date-level effect estimates with uncertainty
4. A spatial comparison or a clear explanation for omitting one
5. Sensitivity checks for timing assumptions, geography, zero fares, and control selection
6. Explicit separation of observed measures, modeled estimates, and assumptions
