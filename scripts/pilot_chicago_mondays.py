"""Compare bounded Monday evening traffic near Wrigley Field."""

from __future__ import annotations

import csv
import argparse
import getpass
import io
import os
import statistics
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATASET_ID = "8bbv-3wbe"
EXPORT_URL = f"https://data.cityofchicago.org/api/v3/views/{DATASET_ID}/export.csv"
COMMUNITY_AREA = "6"  # Lake View; broader than the immediate Wrigley area.
OUTPUT = Path("data/derived/chicago_monday_pilot.csv")
CACHE_DIR = Path("data/cache")
DATE_CONFIG = Path("config/chicago_pilot_dates.csv")


APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")


def request_headers() -> dict[str, str]:
    global APP_TOKEN
    if not APP_TOKEN:
        print("No token found in SOCRATA_APP_TOKEN.", flush=True)
        print("Paste your token at the hidden prompt, then press Enter.", flush=True)
        APP_TOKEN = getpass.getpass("Socrata app token (input hidden): ").strip()
    if not APP_TOKEN:
        raise RuntimeError("A Socrata app token is required for filtered extraction.")
    return {
        "User-Agent": "uber-driver-market-study/1.0",
        "X-App-Token": APP_TOKEN,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date-config",
        type=Path,
        default=DATE_CONFIG,
        help="CSV containing date, group, and note columns",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Summary CSV destination",
    )
    return parser.parse_args()


def load_dates(date_config: Path) -> list[tuple[str, str, str]]:
    with date_config.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    dates = [(row["date"], row["group"], row["note"]) for row in rows]
    if len({date for date, _, _ in dates}) != len(dates):
        raise RuntimeError(f"Duplicate dates found in {date_config}")
    return dates


def fetch_window(date: str) -> list[dict[str, str]]:
    cache_path = CACHE_DIR / f"chicago_tnp_{date}_1600_2359.csv"
    if cache_path.exists():
        print(f"  Loading cached export {cache_path}...", flush=True)
        with cache_path.open(newline="", encoding="utf-8") as cache_file:
            return list(csv.DictReader(cache_file))

    query = (
        "SELECT trip_id, trip_start_timestamp, trip_seconds, trip_miles, fare, "
        "pickup_community_area, dropoff_community_area "
        f"WHERE trip_start_timestamp between '{date}T16:00:00' "
        f"and '{date}T23:59:59' and "
        f"(pickup_community_area='{COMMUNITY_AREA}' or "
        f"dropoff_community_area='{COMMUNITY_AREA}')"
    )
    url = f"{EXPORT_URL}?{urllib.parse.urlencode({'query': query})}"
    request = urllib.request.Request(url, headers=request_headers())
    print(f"  Preparing filtered CSV export for {date}...", flush=True)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8"))
            rows: list[dict[str, str]] = []
            for row_number, row in enumerate(reader, start=1):
                normalized = {
                    key.strip().lower().replace(" ", "_"): value
                    for key, value in row.items()
                }
                rows.append(normalized)
                if row_number % 10_000 == 0:
                    print(f"    Downloaded {row_number:,} matching rows...", flush=True)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Chicago API returned HTTP {error.code}: {detail}") from error
    except TimeoutError as error:
        raise RuntimeError(
            "Chicago's filtered export did not begin within five minutes. The token "
            "was accepted; the portal needs a different partitioning strategy."
        ) from error
    print(f"  Export complete: {len(rows):,} matching rows.", flush=True)
    if rows:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", newline="", encoding="utf-8") as cache_file:
            writer = csv.DictWriter(cache_file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Cached export at {cache_path}.", flush=True)
    return rows


def summarize(rows: list[dict[str, str]], direction: str) -> dict[str, float | int]:
    area_field = f"{direction}_community_area"
    if rows and area_field not in rows[0]:
        available = ", ".join(rows[0].keys())
        raise RuntimeError(f"Expected {area_field}; export columns were: {available}")
    selected = [row for row in rows if row.get(area_field) == COMMUNITY_AREA]

    def parse_number(value: str) -> float:
        return float(value.replace("$", "").replace(",", "").strip())

    def values(field: str) -> list[float]:
        return [
            parse_number(row[field])
            for row in selected
            if row.get(field) not in (None, "")
        ]

    fares = values("fare")
    seconds = values("trip_seconds")
    miles = values("trip_miles")
    return {
        "trips": len(selected),
        "median_fare": statistics.median(fares) if fares else 0,
        "median_trip_seconds": statistics.median(seconds) if seconds else 0,
        "median_trip_miles": statistics.median(miles) if miles else 0,
        "zero_fare_trips": sum(value == 0 for value in fares),
    }


def main() -> None:
    args = parse_args()
    print("Chicago Monday event pilot", flush=True)
    print("The token is used only as a request header and is not saved.", flush=True)
    rows = []
    for date, group, note in load_dates(args.date_config):
        print(f"Requesting {date} 16:00-23:59 from Chicago Open Data...", flush=True)
        window_rows = fetch_window(date)
        if not window_rows:
            print(
                f"  No published rows returned for {date}; excluding it from the summary.",
                flush=True,
            )
            continue
        for direction in ("pickup", "dropoff"):
            summary = summarize(window_rows, direction)
            rows.append(
                {
                    "date": date,
                    "group": group,
                    "direction": direction,
                    "window_local": "16:00-23:59",
                    "community_area": COMMUNITY_AREA,
                    **summary,
                    "matching_rows_exported": len(window_rows),
                    "note": note,
                }
            )

    if not rows:
        raise RuntimeError("No configured dates returned published trip rows.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved pilot summary to {args.output}", flush=True)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
