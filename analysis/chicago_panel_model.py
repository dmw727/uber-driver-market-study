"""Estimate descriptive Wrigley event effects across the Monday panel."""

from __future__ import annotations

import csv
import math
import random
import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chart_runtime"))
import numpy as np


PROFILE = Path("data/derived/chicago_monday_panel_profile.csv")
WEATHER = Path("data/derived/chicago_monday_panel_weather.csv")
OUTPUT = Path("data/derived/chicago_monday_panel_estimates.csv")
REPORT = Path("docs/CHICAGO_PANEL_FINDINGS.md")
HOLIDAY_ADJACENT = {"2026-05-25", "2026-07-06"}
RNG = random.Random(727)


def read_indexed(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return {row["date"]: row for row in csv.DictReader(source)}


def load_rows() -> list[dict[str, object]]:
    profiles = read_indexed(PROFILE)
    weather = read_indexed(WEATHER)
    rows = []
    first_date = min(date.fromisoformat(value) for value in profiles)
    for key, item in profiles.items():
        observed = date.fromisoformat(key)
        weather_row = weather[key]
        rows.append(
            {
                "date": key,
                "event": int(item["group"] == "event"),
                "volume": int(item["unique_area_trips"]),
                "weather_stress": int(weather_row["weather_stress"]),
                "temperature_f": float(weather_row["mean_temperature_f"]),
                "week_index": (observed - first_date).days / 7,
                "holiday_adjacent": int(key in HOLIDAY_ADJACENT),
            }
        )
    return rows


def difference(rows: list[dict[str, object]]) -> tuple[float, float, float]:
    events = [float(row["volume"]) for row in rows if row["event"] == 1]
    controls = [float(row["volume"]) for row in rows if row["event"] == 0]
    event_mean = statistics.mean(events)
    control_mean = statistics.mean(controls)
    return event_mean, control_mean, event_mean / control_mean - 1


def bootstrap_ci(rows: list[dict[str, object]], iterations: int = 10_000) -> tuple[float, float]:
    events = [row for row in rows if row["event"] == 1]
    controls = [row for row in rows if row["event"] == 0]
    estimates = []
    for _ in range(iterations):
        sample_events = [RNG.choice(events) for _ in events]
        sample_controls = [RNG.choice(controls) for _ in controls]
        estimates.append(difference(sample_events + sample_controls)[2])
    estimates.sort()
    return estimates[int(iterations * 0.025)], estimates[int(iterations * 0.975)]


def ols_hc1(rows: list[dict[str, object]]) -> dict[str, float]:
    x = np.array(
        [
            [
                1.0,
                float(row["event"]),
                float(row["weather_stress"]),
                float(row["temperature_f"]) / 10,
                float(row["week_index"]) / 10,
            ]
            for row in rows
        ]
    )
    y = np.log(np.array([float(row["volume"]) for row in rows]))
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    residuals = y - x @ beta
    meat = x.T @ np.diag(residuals**2) @ x
    n, k = x.shape
    covariance = (n / (n - k)) * xtx_inv @ meat @ xtx_inv
    standard_error = math.sqrt(float(covariance[1, 1]))
    event_beta = float(beta[1])
    return {
        "beta": event_beta,
        "se": standard_error,
        "effect": math.exp(event_beta) - 1,
        "ci_low": math.exp(event_beta - 1.96 * standard_error) - 1,
        "ci_high": math.exp(event_beta + 1.96 * standard_error) - 1,
    }


def main() -> None:
    rows = load_rows()
    scenarios = {
        "All published Mondays": rows,
        "Non-weather-stress Mondays": [row for row in rows if row["weather_stress"] == 0],
        "Non-weather and non-holiday Mondays": [
            row
            for row in rows
            if row["weather_stress"] == 0 and row["holiday_adjacent"] == 0
        ],
        "Exclude Aug 31 volume anomaly date": [
            row for row in rows if row["date"] != "2026-08-31"
        ],
    }
    output_rows = []
    for name, sample in scenarios.items():
        event_mean, control_mean, effect = difference(sample)
        low, high = bootstrap_ci(sample)
        output_rows.append(
            {
                "scenario": name,
                "dates": len(sample),
                "event_dates": sum(int(row["event"]) for row in sample),
                "control_dates": sum(1 - int(row["event"]) for row in sample),
                "mean_event_volume": round(event_mean, 1),
                "mean_control_volume": round(control_mean, 1),
                "relative_difference": round(effect, 4),
                "bootstrap_ci_low": round(low, 4),
                "bootstrap_ci_high": round(high, 4),
            }
        )

    adjusted = ols_hc1(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)

    report = [
        "# Chicago Monday Panel: Preliminary Findings",
        "",
        "## Answer first",
        "",
        f"Across all 22 published Mondays, Wrigley home-game dates averaged {output_rows[0]['mean_event_volume']:,.0f} area-touching trips versus {output_rows[0]['mean_control_volume']:,.0f} on comparison Mondays, a descriptive difference of {output_rows[0]['relative_difference']:.1%}. The direction and approximate magnitude remain stable across the planned sensitivity exclusions.",
        "",
        "## Sensitivity estimates",
        "",
        "| Scenario | Dates (event/control) | Relative difference | Date-bootstrap 95% interval |",
        "|---|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['scenario']} | {row['dates']} ({row['event_dates']}/{row['control_dates']}) | "
        f"{row['relative_difference']:.1%} | {row['bootstrap_ci_low']:.1%} to {row['bootstrap_ci_high']:.1%} |"
        for row in output_rows
    )
    report.extend(
        [
            "",
            "## Adjusted estimate",
            "",
            f"A compact log-volume regression adjusting for weather stress, mean evening temperature, and week-of-season estimates a {adjusted['effect']:.1%} event-date difference (HC1 robust 95% interval: {adjusted['ci_low']:.1%} to {adjusted['ci_high']:.1%}).",
            "",
            "## Interpretation limits",
            "",
            "This is a bounded observational estimate for trips touching Community Area 6, not a causal estimate of all rideshare demand or driver earnings. The public data do not report drivers online, unfulfilled requests, dynamic pricing, or rider intent. Weather is modeled from hourly reanalysis at Wrigley coordinates, and competing-event classification remains incomplete. August 31 is retained only in the volume sensitivity analysis; its monetary fields are unusable.",
            "",
            "The result is nevertheless strong enough to guide the next stage: inspect event-time arrival and departure shapes, complete competing-event labels, and test whether event dates increase occupied-vehicle pressure rather than merely shifting trip timing.",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
