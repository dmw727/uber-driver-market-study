"""Profile every available date in the expanded Chicago Monday panel."""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from chicago_pilot_quality import profile, read_rows, time_bins, write_csv


CONFIG = Path("config/chicago_monday_panel_dates.csv")
CACHE_DIR = Path("data/cache")
PROFILE_OUTPUT = Path("data/derived/chicago_monday_panel_profile.csv")
BIN_OUTPUT = Path("data/derived/chicago_monday_panel_15min.csv")
REPORT_OUTPUT = Path("docs/CHICAGO_PANEL_QA.md")


def pct(value: float) -> str:
    return f"{value:.2%}"


def main() -> None:
    with CONFIG.open(newline="", encoding="utf-8") as source:
        config = list(csv.DictReader(source))

    profiles: list[dict[str, object]] = []
    bins: list[dict[str, object]] = []
    unavailable: list[str] = []
    for item in config:
        date = item["date"]
        path = CACHE_DIR / f"chicago_tnp_{date}_1600_2359.csv"
        if not path.exists():
            unavailable.append(date)
            continue
        rows = read_rows(path)
        result = profile(date, rows)
        result.update(
            {
                "date": date,
                "group": item["group"],
                "cubs_home_game": item["cubs_home_game"],
                "note": item["note"],
            }
        )
        result["missing_fares"] = result["missing"]["fare"]
        del result["missing"]
        profiles.append(result)
        bins.extend(time_bins(date, item["group"], rows))

    if not profiles:
        raise RuntimeError("No available Monday panel cache files were found.")
    write_csv(PROFILE_OUTPUT, profiles)
    write_csv(BIN_OUTPUT, bins)

    events = [row for row in profiles if row["group"] == "event"]
    controls = [row for row in profiles if row["group"] == "control"]
    event_volumes = [int(row["unique_area_trips"]) for row in events]
    control_volumes = [int(row["unique_area_trips"]) for row in controls]
    zero_outliers = [row for row in profiles if float(row["zero_fare_rate"]) >= 0.02]
    duplicate_total = sum(int(row["duplicate_trip_ids"]) for row in profiles)
    neither_total = sum(int(row["neither_matches"]) for row in profiles)

    report = [
        "# Chicago Monday Panel: Data-Quality Review",
        "",
        "## Coverage",
        "",
        f"The panel contains {len(profiles)} published Mondays: {len(events)} Cubs home-game dates and {len(controls)} comparison dates. "
        f"The source had not yet published {len(unavailable)} configured September dates when the extract ran.",
        "",
        f"Unavailable dates: {', '.join(unavailable) if unavailable else 'none'}.",
        "",
        "## Date-level checks",
        "",
        "| Date | Group | Unique trips | Zero fares | Missing fares | Duplicate IDs |",
        "|---|---|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['date']} | {row['group']} | {int(row['unique_area_trips']):,} | "
        f"{int(row['zero_fares']):,} ({pct(float(row['zero_fare_rate']))}) | "
        f"{int(row['missing_fares']):,} | {int(row['duplicate_trip_ids']):,} |"
        for row in profiles
    )
    report.extend(
        [
            "",
            "## Distribution check",
            "",
            f"Median event volume is {statistics.median(event_volumes):,.0f} trips versus "
            f"{statistics.median(control_volumes):,.0f} for comparison Mondays. Event-date volume ranges from "
            f"{min(event_volumes):,} to {max(event_volumes):,}; comparison volume ranges from "
            f"{min(control_volumes):,} to {max(control_volumes):,}.",
            "",
            f"Across the panel there are {duplicate_total:,} duplicate trip IDs and {neither_total:,} rows that fail the Community Area 6 filter check.",
            "",
            "Dates with a zero-fare rate of at least 2%: "
            + (
                ", ".join(
                    f"{row['date']} ({pct(float(row['zero_fare_rate']))})"
                    for row in zero_outliers
                )
                if zero_outliers
                else "none"
            )
            + ".",
            "",
            "## Decision",
            "",
            "The panel is ready for covariate enrichment and descriptive modeling, but not yet for a causal claim. Weather, holiday, and competing-event labels must be attached before adjusted comparisons. August 31 monetary outcomes remain excluded because of the confirmed all-zero charge anomaly; its trip counts remain available for volume sensitivity analysis.",
        ]
    )
    REPORT_OUTPUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {PROFILE_OUTPUT} with {len(profiles)} dates.")
    print(f"Wrote {BIN_OUTPUT} with {len(bins)} intervals.")
    print(f"Wrote {REPORT_OUTPUT}.")


if __name__ == "__main__":
    main()
