# Tangential Driving Strategy: Chicago Test

## Question

Do areas adjacent to Wrigley capture event-related pickup demand with less trip-time friction than the Lake View event core?

This question adapts an operating hypothesis developed from the author's experience driving Uber in Nashville. The author previously lived in the Chicago area but did not drive Uber there. Chicago is therefore a public-data test of whether the idea transfers to another market, not a validation of personal Chicago driving experience.

## Clean-weather zone comparison

Pickup demand is normalized per community area. Congestion friction is median occupied minutes per mile. The demand-to-friction measure divides relative pickup uplift by relative friction; it is an operational comparison, not driver profit.

| Zone | Pickup uplift | Friction change | Occupied fare/min change | Demand-to-friction change |
|---|---:|---:|---:|---:|
| core | 47.4% | -6.1% | 2.8% | 57.1% |
| inner_ring | 5.2% | 2.9% | -8.0% | 2.3% |
| outer_ring | 4.3% | 3.8% | -3.7% | 0.5% |

## Preliminary answer

The strongest demand-to-friction change appears in the **core** (57.1%). This result should be interpreted alongside the phase table before recommending a strategy, because a zone may be attractive only during a specific pregame or postgame interval.

## April road-speed validation

The Traffic Tracker extension compares the April 20 home game with three clock-matched April control Mondays. It does not find a broad arterial congestion penalty: mean core inbound speed was about 1% to 2% below control during the pregame, first two game hours, and late-game/postgame phases. The corresponding mean delay was approximately 0.04 to 0.07 minutes per observed arterial segment.

That result narrows the Chicago claim rather than settling the Nashville hypothesis. It suggests that Chicago arterial speeds alone do not explain the case for working tangentially on this date. Nashville and Chicago differ in street networks, transit use, event traffic management, pickup behavior, and the geography of alternative operating zones. The data also omit dispatch-to-pickup travel, side-street crawling, pickup queues, closures, and the time needed to reach an arterial after collecting a passenger. See [CHICAGO_APRIL_TRAFFIC_VALIDATION.md](CHICAGO_APRIL_TRAFFIC_VALIDATION.md).

## Limits

Fare is passenger fare, not driver pay. The trip data omit idle time, deadheading, acceptance rates, unfulfilled requests, surge multipliers, and exact routes. Community areas also differ internally and in size; per-area normalization is only a first control. August 31 remains in pickup counts but is excluded from every monetary metric. The traffic validation contains only one April event date and should not be generalized to the full season.
