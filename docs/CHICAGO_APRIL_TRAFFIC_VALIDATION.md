# April Traffic-Speed Validation

## Decision question

Did road congestion around Wrigley create an access or egress penalty large enough to qualify the apparent event-core pickup opportunity?

This is a Chicago transfer test of a strategy hypothesis developed from the author's Nashville Uber-driving experience. The author lived in the Chicago area but did not drive Uber there; the analysis does not treat local familiarity as Chicago rideshare operating experience.

## Design

April 20, 2026 arterial speeds are matched by segment and clock time to April 6, 13, and 27. A segment is inbound when its recorded direction ends closer to Wrigley Field and outbound when it ends farther away. Core-access segments have midpoints within 1.5 miles; approach-ring segments are 1.5 to 5 miles away.

Invalid speeds and observations without bus/message support are excluded. Reported delay is the change in traversal time for one observed arterial segment, not a full pickup route.

## Results

Because speeds are integer-valued, median pairwise changes often equal zero. Mean pairwise change and the share of intervals running slower preserve the underlying variation.

| Phase | Corridor | Matched intervals | Event mph | Control mph | Mean speed change | Mean delay/segment | Share slower |
|---|---|---:|---:|---:|---:|---:|---:|
| extended_postgame | approach_ring_inbound | 464 | 23.00 | 23.00 | 1.6% | -0.00 min | 40.1% |
| extended_postgame | approach_ring_outbound | 472 | 23.00 | 23.00 | 2.6% | -0.01 min | 39.2% |
| extended_postgame | core_access_inbound | 52 | 21.50 | 23.00 | -0.5% | 0.03 min | 44.2% |
| extended_postgame | core_access_outbound | 60 | 22.00 | 20.50 | 1.6% | 0.01 min | 30.0% |
| game_first_2h | approach_ring_inbound | 1251 | 21.00 | 21.00 | 1.6% | 0.01 min | 39.3% |
| game_first_2h | approach_ring_outbound | 1277 | 21.00 | 20.50 | 3.2% | 0.01 min | 36.6% |
| game_first_2h | core_access_inbound | 145 | 20.00 | 20.00 | -1.9% | 0.06 min | 44.8% |
| game_first_2h | core_access_outbound | 173 | 22.00 | 20.00 | 5.5% | -0.05 min | 31.2% |
| game_late_post_2h | approach_ring_inbound | 1017 | 22.00 | 22.00 | 1.9% | -0.00 min | 39.0% |
| game_late_post_2h | approach_ring_outbound | 1049 | 22.00 | 22.00 | 2.2% | 0.00 min | 40.3% |
| game_late_post_2h | core_access_inbound | 121 | 21.00 | 22.00 | -1.0% | 0.04 min | 39.7% |
| game_late_post_2h | core_access_outbound | 152 | 22.00 | 21.00 | 1.3% | 0.01 min | 40.1% |
| pregame_2h | approach_ring_inbound | 1462 | 20.00 | 20.00 | 0.1% | 0.07 min | 44.5% |
| pregame_2h | approach_ring_outbound | 1385 | 20.00 | 20.00 | 1.8% | 0.02 min | 41.1% |
| pregame_2h | core_access_inbound | 165 | 20.00 | 20.00 | -1.4% | 0.07 min | 41.2% |
| pregame_2h | core_access_outbound | 183 | 21.00 | 20.00 | 2.0% | -0.00 min | 37.7% |

## Interpretation boundary

This is a validation case study, not a season-wide causal estimate or evidence that Chicago and Nashville traffic behave alike. The archive ends April 30, leaving one Cubs home-game Monday and three April controls. Traffic Tracker covers selected arterials and derives estimates from CTA bus GPS traces; it does not observe dispatch-to-pickup time, side-street crawling, queue position, or the driver's actual route.

The traffic results should therefore qualify the full-season occupied-trip findings rather than be merged into a precise driver-profit estimate.

## QA

- Raw observations: 67,304
- Excluded invalid or unsupported observations: 16,843
- Usable observations inside five miles: 40,935
- Matched event segment-intervals: 9,428
- Event observations lacking two controls: 876
