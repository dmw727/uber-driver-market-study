"""Cache April 2026 Traffic Tracker observations around Wrigley Field."""

from __future__ import annotations

import csv
import io
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATASET_ID = "4g9f-3jbs"
RESOURCE_URL = f"https://data.cityofchicago.org/resource/{DATASET_ID}.csv"
OUTPUT_DIR = Path("data/cache/traffic_tracker")
DATES = ("2026-04-06", "2026-04-13", "2026-04-20", "2026-04-27")
FIELDS = (
    "time,segment_id,speed,street,direction,from_street,to_street,length,"
    "bus_count,message_count,start_latitude,start_longitude,end_latitude,end_longitude"
)
PAGE_SIZE = 50_000
MAX_RETRIES = 4

# Covers the event core and practical approach/egress arterials within roughly 5 miles.
BOUNDS = {
    "south": 41.88,
    "north": 42.00,
    "west": -87.75,
    "east": -87.60,
}


def headers() -> dict[str, str]:
    result = {"User-Agent": "uber-driver-market-study/1.0"}
    token = os.environ.get("SOCRATA_APP_TOKEN", "").strip()
    if token:
        result["X-App-Token"] = token
    return result


def fetch_page(date: str, offset: int) -> list[dict[str, str]]:
    bbox = (
        f"((start_latitude between {BOUNDS['south']} and {BOUNDS['north']} "
        f"and start_longitude between {BOUNDS['west']} and {BOUNDS['east']}) or "
        f"(end_latitude between {BOUNDS['south']} and {BOUNDS['north']} "
        f"and end_longitude between {BOUNDS['west']} and {BOUNDS['east']}))"
    )
    query = {
        "$select": FIELDS,
        "$where": (
            f"time between '{date}T16:00:00' and '{date}T23:59:59' and {bbox}"
        ),
        "$order": "time,segment_id",
        "$limit": str(PAGE_SIZE),
        "$offset": str(offset),
    }
    url = f"{RESOURCE_URL}?{urllib.parse.urlencode(query)}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers=headers())
            with urllib.request.urlopen(request, timeout=180) as response:
                return list(csv.DictReader(io.TextIOWrapper(response, encoding="utf-8")))
        except (ConnectionResetError, TimeoutError, urllib.error.URLError) as error:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Traffic download failed for {date} at {offset:,}.") from error
            time.sleep(attempt * 5)
    raise AssertionError("Retry loop ended unexpectedly")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for date in DATES:
        output = OUTPUT_DIR / f"chicago_traffic_segments_{date}_1600_2359.csv"
        if output.exists():
            print(f"Using cached {output}.", flush=True)
            continue
        rows: list[dict[str, str]] = []
        offset = 0
        print(f"Downloading Traffic Tracker records for {date}...", flush=True)
        while True:
            page = fetch_page(date, offset)
            rows.extend(page)
            print(f"  Downloaded {len(rows):,} records...", flush=True)
            if len(page) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        if not rows:
            raise RuntimeError(f"No traffic records returned for {date}.")
        with output.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Cached {len(rows):,} records at {output}.", flush=True)


if __name__ == "__main__":
    main()
