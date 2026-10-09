"""Profile cached Chicago event-pilot exports and produce inspectable evidence."""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path


CACHE_DIR = Path("data/cache")
DERIVED_DIR = Path("data/derived")
REPORT_PATH = Path("docs/CHICAGO_PILOT_QA.md")
CONFIG_PATH = Path("config/chicago_pilot_dates.csv")
COMMUNITY_AREA = "6"
REQUIRED = [
    "trip_id",
    "trip_start_timestamp",
    "trip_seconds",
    "trip_miles",
    "fare",
    "pickup_community_area",
    "dropoff_community_area",
]


def parse_number(value: str) -> float:
    return float(value.replace("$", "").replace(",", "").strip())


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    missing_columns = sorted(set(REQUIRED).difference(rows[0]))
    if missing_columns:
        raise RuntimeError(f"Missing columns in {path}: {missing_columns}")
    return rows


def profile(label: str, rows: list[dict[str, str]]) -> dict[str, object]:
    ids = [row["trip_id"] for row in rows]
    duplicate_ids = len(ids) - len(set(ids))
    missing = {
        field: sum(row.get(field, "") == "" for row in rows) for field in REQUIRED
    }

    numeric_errors = 0
    negative_values = 0
    zero_fares = 0
    for row in rows:
        populated = [
            row[field]
            for field in ("trip_seconds", "trip_miles", "fare")
            if row.get(field, "") != ""
        ]
        try:
            values = [parse_number(value) for value in populated]
        except (ValueError, TypeError):
            numeric_errors += 1
            continue
        negative_values += sum(value < 0 for value in values)
        if row.get("fare", "") != "":
            zero_fares += parse_number(row["fare"]) == 0

    pickup = sum(row["pickup_community_area"] == COMMUNITY_AREA for row in rows)
    dropoff = sum(row["dropoff_community_area"] == COMMUNITY_AREA for row in rows)
    both = sum(
        row["pickup_community_area"] == COMMUNITY_AREA
        and row["dropoff_community_area"] == COMMUNITY_AREA
        for row in rows
    )
    neither = sum(
        row["pickup_community_area"] != COMMUNITY_AREA
        and row["dropoff_community_area"] != COMMUNITY_AREA
        for row in rows
    )

    return {
        "label": label,
        "rows": len(rows),
        "duplicate_trip_ids": duplicate_ids,
        "numeric_parse_errors": numeric_errors,
        "negative_numeric_values": negative_values,
        "zero_fares": zero_fares,
        "zero_fare_rate": zero_fares / len(rows),
        "pickup_matches": pickup,
        "dropoff_matches": dropoff,
        "both_matches": both,
        "unique_area_trips": pickup + dropoff - both,
        "neither_matches": neither,
        "missing": missing,
    }


def time_bins(date: str, group: str, rows: list[dict[str, str]]) -> list[dict[str, object]]:
    pickup_counts: Counter[str] = Counter()
    dropoff_counts: Counter[str] = Counter()
    bucket_rows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        timestamp = datetime.strptime(row["trip_start_timestamp"], "%m/%d/%Y %I:%M:%S %p")
        bucket = timestamp.strftime("%H:%M")
        bucket_rows.setdefault(bucket, []).append(row)
        if row["pickup_community_area"] == COMMUNITY_AREA:
            pickup_counts[bucket] += 1
        if row["dropoff_community_area"] == COMMUNITY_AREA:
            dropoff_counts[bucket] += 1

    output = []
    for bucket in sorted(set(pickup_counts) | set(dropoff_counts)):
        fares = [
            parse_number(row["fare"])
            for row in bucket_rows[bucket]
            if row.get("fare", "") != ""
        ]
        fare_per_mile = [
            parse_number(row["fare"]) / parse_number(row["trip_miles"])
            for row in bucket_rows[bucket]
            if row.get("fare", "") != "" and parse_number(row["trip_miles"]) > 0
        ]
        fare_per_minute = [
            parse_number(row["fare"]) / (parse_number(row["trip_seconds"]) / 60)
            for row in bucket_rows[bucket]
            if row.get("fare", "") != "" and parse_number(row["trip_seconds"]) > 0
        ]
        sorted_fares = sorted(fares)
        p90_index = max(0, int(len(sorted_fares) * 0.9) - 1)
        output.append(
            {
            "date": date,
            "group": group,
            "time_local": bucket,
            "pickup_trips": pickup_counts[bucket],
            "dropoff_trips": dropoff_counts[bucket],
            "unique_trips": len(bucket_rows[bucket]),
            "median_fare": statistics.median(fares) if fares else "",
            "p90_fare": sorted_fares[p90_index] if sorted_fares else "",
            "median_fare_per_mile": statistics.median(fare_per_mile) if fare_per_mile else "",
            "median_fare_per_minute": statistics.median(fare_per_minute) if fare_per_minute else "",
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def pct_change(event: int, control: int) -> str:
    if control == 0:
        return "n/a"
    return f"{(event / control - 1) * 100:.1f}%"


def main() -> None:
    with CONFIG_PATH.open(newline="", encoding="utf-8") as source:
        config_rows = list(csv.DictReader(source))
    datasets = {}
    profiles = {}
    bins = []
    notes = {}
    for config in config_rows:
        date = config["date"]
        group = config["group"]
        path = CACHE_DIR / f"chicago_tnp_{date}_1600_2359.csv"
        rows = read_rows(path)
        datasets[date] = rows
        date_profile = profile(date, rows)
        date_profile["group"] = group
        profiles[date] = date_profile
        bins.extend(time_bins(date, group, rows))
        notes[date] = config["note"]
    write_csv(DERIVED_DIR / "chicago_pilot_15min.csv", bins)

    event_profiles = [item for item in profiles.values() if item["group"] == "event"]
    control_profiles = [item for item in profiles.values() if item["group"] == "control"]
    median_event_volume = statistics.median(
        int(item["unique_area_trips"]) for item in event_profiles
    )
    median_control_volume = statistics.median(
        int(item["unique_area_trips"]) for item in control_profiles
    )
    peak_rows = sorted(
        [row for row in bins if row["group"] == "event"],
        key=lambda row: int(row["pickup_trips"]) + int(row["dropoff_trips"]),
        reverse=True,
    )[:10]
    control_fare_peaks = sorted(
        [
            row
            for row in bins
            if row["group"] == "control" and int(row["unique_trips"]) >= 30
        ],
        key=lambda row: float(row["median_fare"]),
        reverse=True,
    )[:5]

    report = [
        "# Chicago Monday Pilot: Data-Quality Review",
        "",
        "## Dataset and grain",
        "",
        "Each cached row is one public Chicago TNP trip touching Community Area 6 as a pickup, drop-off, or both during 4:00-11:59 PM local time. The expanded pilot contains three Cubs home-game Mondays and four candidate-control Mondays.",
        "",
        "## Core checks",
        "",
        "| Date | Group | Unique trips | Duplicate IDs | Missing fares | Zero fares | Neither-area rows |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {date} | {item['group']} | {item['unique_area_trips']:,} | {item['duplicate_trip_ids']:,} | {item['missing']['fare']:,} | {item['zero_fares']:,} ({item['zero_fare_rate']:.2%}) | {item['neither_matches']:,} |"
        for date, item in profiles.items()
    )
    report.extend(
        [
            "",
            f"Median event-date volume was {median_event_volume:,.0f} trips versus {median_control_volume:,.0f} for controls, an unadjusted difference of {pct_change(int(median_event_volume), int(median_control_volume))}. This is descriptive and precedes control screening and uncertainty estimation.",
            "",
            "Pickup and drop-off counts overlap when a trip begins and ends inside Community Area 6. Unique-area volume therefore uses pickup + drop-off - both, rather than adding directional counts directly.",
            "",
            "## Event timing check",
            "",
            "Highest-volume event-date 15-minute bins:",
            "",
            "| Date | Time | Pickups | Drop-offs |",
            "|---|---|---:|---:|",
        ]
    )
    report.extend(
        f"| {row['date']} | {row['time_local']} | {row['pickup_trips']:,} | {row['dropoff_trips']:,} |"
        for row in peak_rows
    )
    report.extend(
        [
            "",
            "The time profile is a plausibility check, not causal evidence. A credible event pattern should show elevated arrivals before the scheduled start and elevated departures later in the evening.",
            "",
            "## Control-period fare screening",
            "",
            "Highest control-date median-fare bins with at least 30 trips:",
            "",
            "| Date | Time | Trips | Median fare | P90 fare | Median fare/mile | Median fare/minute |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    report.extend(
        f"| {row['date']} | {row['time_local']} | {row['unique_trips']:,} | ${float(row['median_fare']):.2f} | ${float(row['p90_fare']):.2f} | ${float(row['median_fare_per_mile']):.2f} | ${float(row['median_fare_per_minute']):.2f} |"
        for row in control_fare_peaks
    )
    report.extend(
        [
            "",
            "Fare spikes must be checked against trip distance and duration, competing events, weather, and road disruptions. Candidate controls with unexplained anomalies will be rejected or analyzed as secondary event periods.",
            "",
            "## Readiness decision",
            "",
            "**Suitable for expanded exploratory work; not yet suitable for a causal portfolio claim.** The date sample is now adequate for screening consistency, but weather, competing events, road conditions, and the August 31 zero-fare anomaly still require resolution.",
            "",
            "Next: isolate the August 31 fare anomaly, screen all dates for competing events and weather, then estimate date-level event effects and uncertainty.",
        ]
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {DERIVED_DIR / 'chicago_pilot_15min.csv'}")


if __name__ == "__main__":
    main()
