# Data Dictionary

The public dataset contains 51 usable responses from the original 2022 survey. Semicolon-delimited fields represent questions where respondents could select more than one answer.

| Field | Meaning |
|---|---|
| `respondent_id` | Synthetic sequential identifier created for the public dataset |
| `time_of_day` | Recognized time periods when the respondent drove |
| `driver_tenure` | Self-reported length of time driving for Uber |
| `weekly_hours` | Self-reported weekly driving-hour range |
| `hourly_income_before_expenses` | Self-reported gross hourly income range before vehicle and other expenses |
| `high_volume_events` | Recognized event types associated with high demand |
| `local_tourist_ratio` | Self-reported passenger mix |
| `retention_priorities` | Recognized changes selected as ways Uber could improve driver retention |
| `income_expectation` | Standardized assessment of reported income relative to expectations |

## Privacy transformations

The public dataset excludes the original submission ID, submission timestamp, submitter field, market, gender, and all custom free-text comments. One author/test submission without an income-expectation response was also excluded. These removals reduce reidentification risk and do not affect the published analyses.

