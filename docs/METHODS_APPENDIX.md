# Methods Appendix

## Scope and analytical stance

This project combines complementary evidence rather than treating Nashville, Chicago, and New York City as interchangeable markets. Comparisons are descriptive and hypothesis-generating. No result is presented as a causal event effect or a national estimate of driver earnings. Labor and pay regimes are treated as dated market attributes: NYC has a TLC minimum per-trip payment standard; this project identified no Nashville equivalent; and Illinois' sectoral bargaining framework took effect August 7, 2026, after most Chicago panel dates and without implying that those observations were produced under a negotiated agreement.

## Original 2022 survey

- Population: 51 usable self-selected driver responses collected in March-April 2022.
- Recruitment: national and regional Facebook groups for Uber drivers.
- Public-data treatment: names, locations, gender, timestamps, submission identifiers, and custom free text were removed.
- Measures: income relative to expectations, gross hourly-income bands before expenses, tenure, hours, event experience, and retention priorities.
- Primary limits: convenience sampling, small subgroups, historical responses, overlapping multi-select percentages, and no expense-adjusted earnings measure.

## Chicago event panel

- Source: City of Chicago Transportation Network Provider Trips, 2026 partition (`8bbv-3wbe`).
- Window: 4:00 p.m. through 11:59 p.m. on 22 Mondays from April 6 through August 31, 2026.
- Event group: nine Cubs home-game Mondays; comparison group: 13 non-home-game Mondays.
- Geography: Lake View as the event core; deterministic first- and second-order neighboring community-area rings generated from official boundaries.
- Primary volume estimate: event-versus-control difference with a date-level bootstrap confidence interval.
- Sensitivities: non-weather dates, non-weather/non-holiday dates, and exclusion of the August 31 volume anomaly.
- Phase analysis: pregame two hours, first two game hours, late-game/postgame two hours, and the available extended-postgame period, aligned to scheduled first pitch.
- Monetary handling: August 31 remained in volume analysis but was excluded from monetary metrics because 864 records had zero fares, including 792 with zero fare, tip, additional charges, and total despite nonzero trips.
- Limits: passenger fare is not driver pay; no driver identifier, online hours, dispatch time, exact route, or active-supply denominator is available.

## Chicago traffic-speed validation

- Source: Chicago Traffic Tracker historical segment estimates (`4g9f-3jbs`).
- Design: April 20, 2026 home game matched by segment and clock time to April 6, 13, and 27.
- Geography: arterial segments within five miles of Wrigley Field, classified as inbound or outbound from their recorded start and end coordinates; core access was defined as a midpoint within 1.5 miles.
- QA: invalid speeds and observations without bus/message support were excluded.
- Limits: the archive ended April 30, 2026, leaving one event date; estimates derive from CTA-bus GPS traces and do not represent side streets, pickup queues, closures, or actual driver routes.

## NYC driver-cycle benchmark

- Source: NYC TLC April 2025 High-Volume For-Hire Vehicle Parquet file.
- Venue geography: Yankee Stadium coordinates intersect official taxi zone 247, West Concourse. The comparison ring contains taxi-zone polygons within one mile of the core polygon, fixed before outcome analysis.
- Event dates: April 14-16, 2025 Yankees home games at 7:05 p.m.
- Controls: April 7-9, paired by weekday and analyzed using the same 7:05 p.m. phase anchor.
- Retained window: 3:00 p.m. through 11:59 p.m.; reported phases end four hours after first pitch, so no truncated extended-postgame result is shown.
- Metrics: request-to-arrival approach time, arrival-to-pickup waiting time, pickup-to-drop-off occupied time, request-to-drop-off full-cycle time, reported driver pay per occupied hour, and reported driver pay per full-cycle hour.
- QA exclusions: timestamp order violations; approach over 120 minutes; pickup wait over 60 minutes; occupied time outside 1-180 minutes; total cycle outside 1-240 minutes; driver pay outside $0-$500; or distance outside 0-100 miles.
- QA result: 104,381 usable trips from 104,692 trips in the three analysis phases; 311 phase-eligible records were excluded.
- Estimate: for each zone and phase, event/control changes were calculated within three weekday pairs and summarized by the median paired change.
- Limits: completed trips only; no online idle time before request; reported driver pay excludes expenses; NYC's minimum per-trip payment formula may compress driver-pay variation; regulation and transportation conditions limit transferability.

## NYC surge-spillover strategy test

- Question: during the two-hour pregame window, do pickups in the event spillover area that move away from the stadium combine an event-associated pay premium with shorter complete cycles?
- Event sample: April 14-16, 2025, 5:05-7:05 p.m.
- Normal-rate sample: nine Monday-Wednesday pregame-clock windows on April 7-9, 21-23, and 28-30, when the Yankees were away.
- Direction classes: stadium-bound trips begin in the one-mile ring and end in the core; spillover-local trips begin and end in the ring; spillover-away trips begin in the ring, end outside it, and finish at least one-quarter mile farther from the stadium based on official taxi-zone centroids.
- Normal-rate models: separate ordinary least-squares models of log reported driver pay and log passenger base fare, trained only on controls. Features include platform, pickup zone, weekday, 15-minute slot, trip-direction class, log miles, log occupied time, log approach time, and log pickup-wait time.
- Premium estimate: median event actual-to-model ratio divided by the corresponding median control ratio, minus one. This is an implied event-associated premium, not a reported surge multiplier.
- Throughput measures: theoretical cycles per two hours equals 120 divided by median request-to-drop-off minutes. The gross-capacity proxy equals two times median completed-cycle pay per hour.
- Limits: no driver identifier, exact route, displayed surge multiplier, time waiting for the next request, repositioning after drop-off, cancellations, or expenses. NYC's minimum per-trip payment formula means a near-zero driver-pay premium cannot be interpreted as evidence that an unregulated market would behave the same way. Control dates exclude Yankees home games but were not proven free of every local event or source of chaotic demand.

## Metric definitions

| Metric | Definition |
|---|---|
| Pickup uplift | Relative change in pickup count versus clock-matched controls |
| Occupied pay per hour | Reported driver pay divided by pickup-to-drop-off time |
| Full-cycle pay per hour | Reported driver pay divided by request-to-drop-off time |
| Unpaid overhead share | Approach plus pickup-wait minutes divided by request-to-drop-off minutes |
| Engaged vehicle-bin equivalent | Occupied trip minutes allocated across 15-minute bins; a workload proxy, not a count of distinct drivers |

## Reproducibility

The analysis scripts read saved configuration files and write derived CSVs and documentation. Large source extracts remain ignored from version control; bounded derived outputs, configuration, source definitions, and code are retained. The source registry records dataset identity, grain, period, access method, status, and material limitations.

Run the public workflow from the repository root:

```powershell
python analysis/analyze_survey.py
python analysis/create_charts.py
python analysis/chicago_panel_quality.py
python analysis/chicago_panel_model.py
python analysis/chicago_event_time_pressure.py
python analysis/chicago_spatial_opportunity.py
python analysis/chicago_april_traffic_validation.py
python analysis/nyc_yankee_driver_cycle.py
python analysis/nyc_surge_spillover_strategy.py
python analysis/create_extension_charts.py
python -m unittest discover -s tests
```

Network extraction scripts and required credentials are documented separately from the public analytical rerun. See [THREE_CITY_EXTENSION.md](THREE_CITY_EXTENSION.md) and [`config/source_registry.csv`](../config/source_registry.csv).
