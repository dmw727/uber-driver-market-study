"""Estimate pickup-cohort engaged vehicle equivalents from public trip records."""

from __future__ import annotations

import csv
import argparse
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


CONFIG = Path("config/chicago_pilot_dates.csv")
CACHE_DIR = Path("data/cache")
OUTPUT = Path("data/derived/chicago_engaged_vehicle_bounds.csv")
COMMUNITY_AREA = "6"
WINDOW_START_HOUR = 16
WINDOW_END_HOUR = 24
BIN_MINUTES = 15
ASSUMPTIONS = {
    "bin_start": 0.0,
    "bin_midpoint": 7.5,
    "bin_end": 15.0,
}


def parse_number(value: str) -> float:
    return float(value.replace("$", "").replace(",", "").strip())


def floor_bin(timestamp: datetime) -> datetime:
    minute = timestamp.minute - timestamp.minute % BIN_MINUTES
    return timestamp.replace(minute=minute, second=0, microsecond=0)


def overlap_minutes(
    trip_start: datetime,
    trip_end: datetime,
    bin_start: datetime,
) -> float:
    bin_end = bin_start + timedelta(minutes=BIN_MINUTES)
    overlap_start = max(trip_start, bin_start)
    overlap_end = min(trip_end, bin_end)
    return max(0.0, (overlap_end - overlap_start).total_seconds() / 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def load_config(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return {row["date"]: row for row in csv.DictReader(source)}


def load_pickups(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return [
            row
            for row in csv.DictReader(source)
            if row.get("pickup_community_area") == COMMUNITY_AREA
        ]


def estimate_date(
    date: str,
    group: str,
    rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    date_start = datetime.strptime(date, "%Y-%m-%d")
    analysis_start = date_start + timedelta(hours=WINDOW_START_HOUR)
    analysis_end = date_start + timedelta(hours=WINDOW_END_HOUR)

    pickups_by_bin: dict[datetime, int] = defaultdict(int)
    occupied_minutes: dict[tuple[str, datetime], float] = defaultdict(float)
    durations = sorted(parse_number(row["trip_seconds"]) for row in rows)
    p99_duration_seconds = durations[max(0, math.ceil(len(durations) * 0.99) - 1)]
    warmup_minutes = math.ceil(p99_duration_seconds / (BIN_MINUTES * 60)) * BIN_MINUTES
    warmup_end = analysis_start + timedelta(minutes=warmup_minutes)

    for row in rows:
        reported_start = datetime.strptime(
            row["trip_start_timestamp"], "%m/%d/%Y %I:%M:%S %p"
        )
        if not analysis_start <= reported_start < analysis_end:
            continue
        duration = parse_number(row["trip_seconds"])
        pickups_by_bin[floor_bin(reported_start)] += 1

        for assumption, offset_minutes in ASSUMPTIONS.items():
            trip_start = reported_start + timedelta(minutes=offset_minutes)
            trip_end = trip_start + timedelta(seconds=duration)
            current_bin = floor_bin(trip_start)
            while current_bin < min(trip_end, analysis_end):
                occupied_minutes[(assumption, current_bin)] += overlap_minutes(
                    trip_start, trip_end, current_bin
                )
                current_bin += timedelta(minutes=BIN_MINUTES)

    output = []
    current_bin = analysis_start
    while current_bin < analysis_end:
        row: dict[str, object] = {
            "date": date,
            "group": group,
            "time_local": current_bin.strftime("%H:%M"),
            "pickup_trips": pickups_by_bin[current_bin],
            "coverage_status": (
                "warmup_incomplete" if current_bin < warmup_end else "post_p99_warmup"
            ),
            "p99_trip_duration_minutes": round(p99_duration_seconds / 60, 1),
        }
        estimates = []
        for assumption in ASSUMPTIONS:
            value = occupied_minutes[(assumption, current_bin)] / BIN_MINUTES
            row[f"engaged_vehicles_{assumption}"] = round(value, 2)
            estimates.append(value)
        row["engaged_vehicle_min"] = round(min(estimates), 2)
        row["engaged_vehicle_max"] = round(max(estimates), 2)
        midpoint = float(row["engaged_vehicles_bin_midpoint"])
        row["pickups_per_engaged_vehicle_midpoint"] = (
            round(int(row["pickup_trips"]) / midpoint, 3) if midpoint else ""
        )
        output.append(row)
        current_bin += timedelta(minutes=BIN_MINUTES)
    return output


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    results: list[dict[str, object]] = []
    for date, details in config.items():
        cache_path = CACHE_DIR / f"chicago_tnp_{date}_1600_2359.csv"
        if not cache_path.exists():
            print(f"Skipping uncached date: {date}")
            continue
        pickups = load_pickups(cache_path)
        results.extend(estimate_date(date, details["group"], pickups))

    if not results:
        raise RuntimeError("No configured Chicago cache files were found.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {args.output} with {len(results):,} interval rows.")


if __name__ == "__main__":
    main()
