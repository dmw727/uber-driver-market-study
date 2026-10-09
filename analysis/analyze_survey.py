"""Reproduce the published summaries from the anonymized survey data."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "uber_driver_survey_anonymized.csv"
OUTPUT_DIR = ROOT / "outputs"


def read_rows(path: Path = DATA_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_selections(value: str) -> list[str]:
    return [item for item in value.split(";") if item]


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def analyze(rows: list[dict[str, str]]) -> None:
    expectation_order = [
        "Exceeded expectations",
        "Met expectations",
        "Close, but below expectations",
        "Not close to expectations",
    ]
    expectation_counts = Counter(row["income_expectation"] for row in rows)
    total = len(rows)
    met_or_exceeded = expectation_counts["Exceeded expectations"] + expectation_counts["Met expectations"]
    below = total - met_or_exceeded

    headline = [
        {"metric": "Usable responses", "value": total, "percent": ""},
        {
            "metric": "Met or exceeded income expectations",
            "value": met_or_exceeded,
            "percent": f"{met_or_exceeded / total:.1%}",
        },
        {
            "metric": "Fell below income expectations",
            "value": below,
            "percent": f"{below / total:.1%}",
        },
    ]
    write_rows(OUTPUT_DIR / "headline_metrics.csv", ["metric", "value", "percent"], headline)

    expectation_rows = [
        {
            "income_expectation": label,
            "responses": expectation_counts[label],
            "percent": f"{expectation_counts[label] / total:.1%}",
        }
        for label in expectation_order
    ]
    write_rows(
        OUTPUT_DIR / "income_expectations.csv",
        ["income_expectation", "responses", "percent"],
        expectation_rows,
    )

    retention_counts = Counter(
        option for row in rows for option in split_selections(row["retention_priorities"])
    )
    retention_rows = [
        {"retention_priority": label, "respondents": count, "percent_of_respondents": f"{count / total:.1%}"}
        for label, count in retention_counts.most_common()
    ]
    write_rows(
        OUTPUT_DIR / "retention_priorities.csv",
        ["retention_priority", "respondents", "percent_of_respondents"],
        retention_rows,
    )

    by_tenure: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_tenure[row["driver_tenure"]][row["income_expectation"]] += 1
    tenure_rows = []
    for tenure in ["<1 year", "1-3 years", "3-5 years", ">5 years"]:
        counts = by_tenure[tenure]
        group_total = sum(counts.values())
        group_met = counts["Exceeded expectations"] + counts["Met expectations"]
        tenure_rows.append(
            {
                "driver_tenure": tenure,
                "responses": group_total,
                "met_or_exceeded": group_met,
                "met_or_exceeded_percent": f"{group_met / group_total:.1%}",
            }
        )
    write_rows(
        OUTPUT_DIR / "expectations_by_tenure.csv",
        ["driver_tenure", "responses", "met_or_exceeded", "met_or_exceeded_percent"],
        tenure_rows,
    )

    income_counts = Counter(row["hourly_income_before_expenses"] or "Not reported" for row in rows)
    income_order = [
        "$10-$15 dollars",
        "$15-$20 dollars",
        "$20-$25 dollars",
        "$25-$30 dollars",
        "$30-$35 dollars",
        "$35-$40 dollars",
        "$40-$45 dollars",
        "$45-$50 dollars",
        "$50+ dollars",
        "Not reported",
    ]
    income_rows = [
        {"income_band_before_expenses": label, "responses": income_counts[label]}
        for label in income_order
        if income_counts[label]
    ]
    write_rows(
        OUTPUT_DIR / "income_distribution.csv",
        ["income_band_before_expenses", "responses"],
        income_rows,
    )


if __name__ == "__main__":
    analyze(read_rows())
    print(f"Wrote reproducible summaries to {OUTPUT_DIR}")

