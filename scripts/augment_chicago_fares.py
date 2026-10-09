"""Fetch charge fields needed to investigate a date-level fare anomaly."""

from __future__ import annotations

import argparse
import csv
import getpass
import io
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATASET_ID = "8bbv-3wbe"
EXPORT_URL = f"https://data.cityofchicago.org/api/v3/views/{DATASET_ID}/export.csv"
COMMUNITY_AREA = "6"
DEFAULT_DATE = "2026-08-31"
OUTPUT_DIR = Path("data/cache")


def request_headers() -> dict[str, str]:
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if not token:
        print("No token found in SOCRATA_APP_TOKEN.", flush=True)
        print("Paste your token at the hidden prompt, then press Enter.", flush=True)
        token = getpass.getpass("Socrata app token (input hidden): ").strip()
    if not token:
        raise RuntimeError("A Socrata app token is required for filtered extraction.")
    return {
        "User-Agent": "uber-driver-market-study/1.0",
        "X-App-Token": token,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Chicago TNP charge details for one evening."
    )
    parser.add_argument("--date", default=DEFAULT_DATE, help="Date in YYYY-MM-DD format")
    return parser.parse_args()


def fetch(date: str) -> list[dict[str, str]]:
    query = (
        "SELECT trip_id, trip_start_timestamp, trip_seconds, trip_miles, fare, "
        "tip, additional_charges, trip_total, pickup_community_area, "
        "dropoff_community_area "
        f"WHERE trip_start_timestamp between '{date}T16:00:00' "
        f"and '{date}T23:59:59' and "
        f"(pickup_community_area='{COMMUNITY_AREA}' or "
        f"dropoff_community_area='{COMMUNITY_AREA}')"
    )
    url = f"{EXPORT_URL}?{urllib.parse.urlencode({'query': query})}"
    request = urllib.request.Request(url, headers=request_headers())
    print(f"Preparing charge-detail export for {date}...", flush=True)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            reader = csv.DictReader(io.TextIOWrapper(response, encoding="utf-8"))
            rows: list[dict[str, str]] = []
            for row_number, row in enumerate(reader, start=1):
                rows.append(
                    {
                        key.strip().lower().replace(" ", "_"): value
                        for key, value in row.items()
                    }
                )
                if row_number % 10_000 == 0:
                    print(f"  Downloaded {row_number:,} rows...", flush=True)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Chicago API returned HTTP {error.code}: {detail}") from error
    except TimeoutError as error:
        raise RuntimeError(
            "Chicago's filtered export did not begin within five minutes."
        ) from error
    return rows


def parse_money(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value.replace("$", "").replace(",", "").strip())


def summarize(rows: list[dict[str, str]]) -> None:
    zero_fare_rows = [row for row in rows if parse_money(row.get("fare")) == 0]
    zero_total = sum(parse_money(row.get("trip_total")) == 0 for row in zero_fare_rows)
    positive_total = sum(
        (parse_money(row.get("trip_total")) or 0) > 0 for row in zero_fare_rows
    )
    missing_total = sum(row.get("trip_total") in (None, "") for row in zero_fare_rows)
    print(f"Exported {len(rows):,} trips.", flush=True)
    print(f"Zero-fare trips: {len(zero_fare_rows):,}", flush=True)
    print(f"  Positive trip total: {positive_total:,}", flush=True)
    print(f"  Zero trip total: {zero_total:,}", flush=True)
    print(f"  Missing trip total: {missing_total:,}", flush=True)


def main() -> None:
    args = parse_args()
    rows = fetch(args.date)
    if not rows:
        raise RuntimeError("The export returned no matching rows.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"chicago_tnp_{args.date}_fare_detail.csv"
    with output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved charge details to {output}.", flush=True)
    summarize(rows)


if __name__ == "__main__":
    main()
