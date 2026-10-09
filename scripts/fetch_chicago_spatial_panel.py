"""Fetch bounded Monday trips touching the deterministic Wrigley spatial rings."""

from __future__ import annotations

import csv
import getpass
import io
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATASET_ID = "8bbv-3wbe"
EXPORT_URL = f"https://data.cityofchicago.org/api/v3/views/{DATASET_ID}/export.csv"
DATE_CONFIG = Path("config/chicago_monday_panel_dates.csv")
ZONE_CONFIG = Path("config/wrigley_spatial_rings.csv")
CACHE_DIR = Path("data/cache/spatial_panel")
FIELDS = [
    "trip_id",
    "trip_start_timestamp",
    "trip_seconds",
    "trip_miles",
    "fare",
    "tip",
    "additional_charges",
    "trip_total",
    "pickup_community_area",
    "dropoff_community_area",
]
PAGE_SIZE = 10_000
MAX_RETRIES = 4


def request_headers() -> dict[str, str]:
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if not token:
        token = getpass.getpass("Socrata app token (input hidden): ").strip()
    if not token:
        raise RuntimeError("A Socrata app token is required.")
    return {"User-Agent": "uber-driver-market-study/1.0", "X-App-Token": token}


def read_dates() -> list[str]:
    with DATE_CONFIG.open(newline="", encoding="utf-8") as source:
        return [row["date"] for row in csv.DictReader(source) if row["date"] <= "2026-08-31"]


def read_areas() -> list[str]:
    with ZONE_CONFIG.open(newline="", encoding="utf-8") as source:
        return [row["community_area"] for row in csv.DictReader(source)]


def fetch_page(
    base_query: str,
    offset: int,
    headers: dict[str, str],
) -> list[dict[str, str]]:
    query = f"{base_query} ORDER BY trip_id LIMIT {PAGE_SIZE} OFFSET {offset}"
    url = f"{EXPORT_URL}?{urllib.parse.urlencode({'query': query})}"
    for attempt in range(1, MAX_RETRIES + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8"))
                return [
                    {
                        key.strip().lower().replace(" ", "_"): value
                        for key, value in row.items()
                    }
                    for row in reader
                ]
        except (ConnectionResetError, TimeoutError, urllib.error.URLError) as error:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Chicago export failed at offset {offset:,} after {MAX_RETRIES} attempts."
                ) from error
            wait_seconds = attempt * 5
            print(
                f"  Page at offset {offset:,} was interrupted; retrying in "
                f"{wait_seconds} seconds ({attempt}/{MAX_RETRIES})...",
                flush=True,
            )
            time.sleep(wait_seconds)
    raise AssertionError("Retry loop ended unexpectedly")


def fetch(date: str, areas: list[str], headers: dict[str, str]) -> list[dict[str, str]]:
    area_values = ",".join(f"'{area}'" for area in areas)
    base_query = (
        f"SELECT {', '.join(FIELDS)} "
        f"WHERE trip_start_timestamp between '{date}T16:00:00' and '{date}T23:59:59' "
        f"and (pickup_community_area in ({area_values}) or "
        f"dropoff_community_area in ({area_values}))"
    )
    print(f"Preparing spatial export for {date}...", flush=True)
    rows = []
    offset = 0
    while True:
        page = fetch_page(base_query, offset, headers)
        rows.extend(page)
        print(f"  Downloaded {len(rows):,} rows...", flush=True)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def main() -> None:
    areas = read_areas()
    headers: dict[str, str] | None = None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for date in read_dates():
        output = CACHE_DIR / f"chicago_tnp_rings_{date}_1600_2359.csv"
        if output.exists():
            print(f"Using cached {output}.", flush=True)
            continue
        if headers is None:
            headers = request_headers()
        rows = fetch(date, areas, headers)
        if not rows:
            print(f"  No published rows returned for {date}; skipping.", flush=True)
            continue
        with output.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Cached {len(rows):,} rows at {output}.", flush=True)


if __name__ == "__main__":
    main()
