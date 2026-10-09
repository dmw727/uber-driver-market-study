# Three-City Extension: Driver Experience, Event Demand, and Trip Economics

## Purpose

This extension asks whether the concerns raised in the original 2022 driver survey are visible in larger public evidence from Nashville, Chicago, and New York City.

The cities are not treated as interchangeable markets. Each contributes a different kind of evidence:

- **Nashville** supplies local context, Tennessee survey research, and a recent event-zone pilot.
- **Chicago** supplies trip-level operational data suitable for estimating event-related changes in demand and trip conditions.
- **New York City** supplies trip-level driver-pay data and a regulated-market benchmark.

The analysis will triangulate findings across sources. It will not pool the records into a single city ranking or imply that a measure from one city is equivalent to a different measure from another.

## Decision Question

What can public market data tell us about the conditions behind drivers' reported concerns about earnings expectations and retention?

## Analytical Questions

### 1. Driver perspective

What did surveyed drivers say about earnings expectations and retention priorities?

Evidence:

- Original 2022 survey: 51 usable driver responses
- Tennessee Department of Transportation 2019 ridesourcing survey aggregates

### 2. Event demand in Chicago

How do major events change rideshare volume and observable trip economics near venues relative to comparable non-event periods?

Candidate measures:

- Trips per 15-minute interval
- Median fare and tip per trip
- Median trip duration and distance
- Fare per trip minute and per trip mile
- Pickup and drop-off concentration by community area
- Event-window uplift relative to matched weekday, time, season, and location baselines

Interpretation boundary: passenger fares and tips do not equal driver net earnings. Event demand may rise while congestion reduces the number of trips a driver can complete.

### 3. Driver pay in New York City

How do reported driver payments vary by time, trip duration, distance, location, and platform in a regulated market?

Candidate measures:

- Driver pay per trip
- Driver pay per passenger minute and mile
- Request-to-pickup and pickup-to-drop-off time where supported
- Platform and zone variation
- Distributional results, not only averages

Interpretation boundary: New York's minimum-pay rules and transportation system make it a benchmark, not a national estimate.

Current benchmark: three April 14-16, 2025 Yankee Stadium event evenings are matched by weekday to April 7-9 controls. The analysis separates request-to-arrival, arrival-to-pickup, and occupied time, then compares occupied-only and full-cycle driver-pay rates. See [NYC_YANKEE_DRIVER_CYCLE.md](NYC_YANKEE_DRIVER_CYCLE.md).

### 4. Nashville operational context

What local evidence supports or complicates the original survey's claims?

Current evidence:

- TDOT's 2019 survey included 996 weighted Tennessee respondents, including 459 from Nashville.
- Driver appendices reported 41 active-driver and 28 former-driver responses.
- The 2025 TPAC rideshare-zone pilot reported a 6% increase in drop-offs, less than a 1% decrease in pickups, and slightly reduced cancellations using Uber heatmaps.

Interpretation boundary: the underlying TDOT and Uber records are not currently available as public microdata. Published aggregates can provide context but cannot be analyzed as though respondent-level or trip-level files were available.

## Common Measurement Framework

| Concept | Preferred measure | Available evidence |
|---|---|---|
| Earnings expectations | Self-reported relationship between income and expectations | Original survey |
| Retention priorities | Respondent-selected changes and reasons former drivers stopped | Original survey and TDOT aggregates |
| Demand intensity | Trips per place and time interval relative to a matched baseline | Chicago |
| Passenger spending | Fare and tip per trip, minute, and mile | Chicago |
| Driver compensation | Platform-reported driver pay per trip, passenger minute, and mile | New York City |
| Friction | Duration, congestion proxies, unpaid or unengaged time where available | All three, with different definitions |
| Event operations | Changes near venues and designated pickup areas | Chicago and Nashville TPAC pilot |

Measures will retain their source-specific names. Passenger fare will never be relabeled as driver pay, and trip-level pay will never be relabeled as net hourly earnings.

### Chicago supply limitation

No identified public Chicago source reports the number of drivers logged into a platform by Community Area and 15-minute interval. The TNP Drivers dataset is driver-month grain and includes monthly trip counts plus the driver's reported home geography; it does not locate the driver while working or report online hours.

The event analysis may therefore report:

- Monthly citywide active-driver context from the Drivers dataset
- Trips beginning or ending in the study area by 15-minute interval
- Occupied-trip minutes as an engaged-activity proxy
- Fare, distance, and duration distributions as possible demand-pressure indicators

None of these measures will be labeled “drivers online.” Trip records do not contain a driver identifier, so they cannot establish how many distinct drivers served the area. A direct supply denominator would require provider data or a targeted public-records request containing anonymized platform-online counts by place and time.

## Initial Chicago Design

The first operational analysis will use a small, auditable event sample rather than an entire year of data.

Candidate venue types:

- Wrigley Field: recurring baseball events in a dense neighborhood
- United Center: arena events with concentrated arrival and departure periods
- Soldier Field: large but less frequent stadium events
- McCormick Place: conventions with longer and less sharply bounded demand windows

For each selected event:

1. Define the venue's pickup and drop-off geography before inspecting outcomes.
2. Define arrival and departure windows from the scheduled start and expected end times.
3. Select comparison dates matching weekday, hour, month or season, and venue geography.
4. Compare volume, fare, tip, duration, and distance distributions.
5. Run sensitivity checks using alternate event windows and comparison dates.
6. Report both demand benefits and congestion-related costs visible in the data.

## Pilot-to-Production Gate

The first pass is a feasibility pilot. Its purpose is to confirm the source schema, geographic mapping, event-window logic, missingness, and practical query size. Pilot findings are exploratory and will not be presented as final evidence.

Before producing portfolio findings, freeze a short analysis protocol containing:

- Exact dataset IDs, extraction dates, query text, and covered date range
- Venue geography and event windows defined without looking at outcome differences
- At least three matched non-event dates per event, using the same weekday, time band, season, and geography
- Multiple event dates wherever the schedule permits; millions of trips from one event do not create multiple independent events
- Date- or event-level uncertainty estimates so individual trips are not treated as independent evidence of an event effect
- Primary metrics selected in advance, with secondary metrics labeled exploratory
- Missing-value, duplicate, impossible-value, and late-revision checks
- Explicit handling for rounded 15-minute timestamps, zero-dollar records, and percentage fields outside their expected range
- Sensitivity checks for alternate time windows, comparison dates, and pickup versus drop-off definitions
- Fare-spike screening on event and non-event dates, including investigation of unexplained control-period anomalies
- Trip-mix adjustment using distance, duration, fare per mile, and fare per minute so longer trips are not mistaken for price pressure

The production sample will be determined by independent dates and events, not by an arbitrary trip-row target. After the pilot supplies plausible variance and event-effect estimates, the event count can be adjusted using a power or precision analysis. If there are too few comparable events, the result will remain a carefully labeled case study rather than an overclaimed citywide estimate.

### Production-readiness checks

Advance beyond the pilot only when:

1. The official API fields and date coverage are verified against portal metadata.
2. A small repeated query returns stable counts or any revision behavior is documented.
3. Venue geography produces credible trips when checked against known neighborhood patterns.
4. Event and control windows have adequate trip counts in every interval used for comparison.
5. The analysis can be rerun from a saved configuration without manual filtering.
6. Tables, figures, and written claims can be traced to a source query and analysis version.

Candidate control periods will be rejected or explicitly labeled when they contain unexplained volume or fare anomalies. A non-event label means only that no selected target event is known; it does not prove that the period was operationally ordinary.

## Role of Personal Experience

Firsthand familiarity with Chicago and Nashville will inform hypotheses, venue selection, data-quality checks, and interpretation. It will not substitute for missing measurements or turn city-specific results into national claims.

Examples of appropriate use:

- Identifying streets, venues, or travel patterns that require closer validation
- Explaining why two locations with similar trip counts may operate differently
- Recognizing implausible geographic mappings or event windows
- Supplying questions that the quantitative analysis should test

Examples of inappropriate use:

- Filling missing values from memory
- Treating remembered conditions as measured historical facts
- Generalizing one neighborhood or period to an entire city

## Stop Conditions

The extension should remain portfolio-efficient. Stop expanding when it has:

- One defensible Chicago event comparison with sensitivity checks
- One focused NYC driver-pay benchmark
- A Nashville context section grounded in published local evidence
- A clear synthesis showing where operational data supports, complicates, or cannot answer the original driver concerns

Additional cities, predictive models, and live polling are outside the initial scope.

## Official Sources

- Chicago Transportation Network Provider Trips (2026; preferred extraction partition): https://data.cityofchicago.org/d/8bbv-3wbe
- Chicago Transportation Network Provider Trips (2025-present combined view): https://data.cityofchicago.org/d/6dvr-xwnh
- Chicago Transportation Network Provider Trips (2023-2024): https://data.cityofchicago.org/d/n26f-ihde
- NYC TLC Trip Record Data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- NYC High-Volume FHV data dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf
- TDOT ridesourcing study: https://www.tn.gov/content/dam/tn/tdot/research/final-reports/res2020-final-reports/RES2020-20_Final_Report_approved.pdf
- Nashville TPAC pilot staff analysis: https://www.nashville.gov/sites/default/files/2025-04/TPC_StaffAnalysis_April2025.pdf

