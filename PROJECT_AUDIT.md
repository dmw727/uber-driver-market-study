# Uber Driver Market Study: Portfolio Audit

## Project purpose

This project began as a 2022 capstone motivated by firsthand experience as an Uber driver. The original goal was to understand why driver earnings and satisfaction varied and to identify changes that drivers believed would improve retention.

The portfolio version should preserve that origin. It will present a transparent reanalysis of the original survey rather than pretend the data is current, representative, or capable of proving causal effects.

## Original evidence reviewed

- Final capstone paper: `Wood_Organizational Project Paper Final.docx`
- Survey workbook: `Uber research study.xlsx`
- Decision-support presentation: `Decision Support System for Uber Technologies Incorporated.pptx`

The college archive remains unchanged. The original workbook should not be committed because it contains submission IDs, timestamps, an author/test response, and unstructured comments that may carry identifying details.

The final paper itself is suitable to publish as historical context. The repository includes an unchanged copy in both Word and PDF formats so readers can compare the original submission with the later reanalysis.

## What the work proves

- Original survey design and primary research
- Collection of responses from drivers in multiple United States markets
- Excel summaries, pivot-style analysis, formulas, and charts
- Translation of survey findings into operational recommendations
- Business writing and stakeholder communication
- Domain knowledge grounded in firsthand experience

## Verified baseline

The workbook contains 52 submitted rows. One identifiable author/test row has several unanswered fields, leaving 51 usable responses for the income-expectation question.

Among those 51 responses:

| Income relative to expectations | Responses |
|---|---:|
| Exceeded expectations | 5 |
| Met expectations | 22 |
| Close, but below expectations | 16 |
| Not close to expectations | 8 |

Therefore, 27 of 51 respondents (52.9%) reported meeting or exceeding expectations, while 24 of 51 (47.1%) reported falling short. This supports the paper's rounded 53% versus 47% statement, but the usable denominator must be stated explicitly.

The most frequently selected retention ideas were:

| Driver-selected idea | Selections |
|---|---:|
| Increase rates | 42 |
| More promotions or opportunities | 32 |
| Allow customers to request a driver | 18 |
| Improve driver safety features | 18 |
| Add local support offices | 17 |

This was a multiple-response question. Counts and percentages describe selections or respondents choosing each option; they must not be treated as shares of one mutually exclusive total.

## Problems to correct

1. **Sampling limits:** respondents were recruited from Facebook driver groups, producing a small self-selected convenience sample. Results cannot represent all Uber drivers.
2. **Inconsistent denominators:** the paper reports 52 participants even when an item has only 51 usable responses.
3. **Manual calculations:** several summary values are typed directly into the workbook, and some formulas use hard-coded numbers.
4. **Unsupported causal claims:** the survey can describe driver opinions, but it cannot prove that a recommendation will increase retention or Uber revenue.
5. **Ambiguous earnings measure:** respondents reported income ranges before expenses. These values are neither net earnings nor profit.
6. **Multi-select interpretation:** recommendation counts overlap because respondents could choose several options.
7. **Messy categories:** market names, whitespace, spelling, and free-text additions require documented cleaning.
8. **Dated external context:** the literature and company information describe conditions around 2018-2022 and should be labeled historical or refreshed.
9. **Presentation mismatch:** the 28-slide decision-support deck is broad and generic. It should remain background material rather than become the public-facing case study.

## Recommended portfolio version

Create a concise historical case study titled **What 51 Uber Drivers Said About Earnings Expectations and Retention**.

The public project should contain:

- A README explaining the personal motivation, question, data, method, findings, limitations, and recommendations
- An anonymized analytical dataset with submission metadata and identifying free text removed
- A reproducible Python or SQL analysis that rebuilds every published figure from the cleaned data
- Three or four restrained charts focused on expectations, retention priorities, tenure, and reported pre-expense income ranges
- A data dictionary and cleaning log
- A short note distinguishing the original 2022 capstone from the later portfolio reanalysis

The original report and workbook remain historical source material. They should not be silently replaced or presented as newly collected research.

## Decision boundary

The study is strong enough to become a featured business-analysis project after the calculations are rebuilt and the limitations are made prominent. It should not be published in its current academic form.

