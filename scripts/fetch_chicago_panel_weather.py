"""Fetch hourly weather covariates aligned to each available Monday trip window."""

from __future__ import annotations

import csv
import json
import statistics
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path


LATITUDE = 41.9484
LONGITUDE = -87.6553
TIMEZONE = "America/Chicago"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
PANEL_PROFILE = Path("data/derived/chicago_monday_panel_profile.csv")
OUTPUT = Path("data/derived/chicago_monday_panel_weather.csv")
SOURCE_URL = "https://open-meteo.com/en/docs/historical-weather-api"
HOURLY_FIELDS = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_gusts_10m",
]


def load_dates() -> list[str]:
    with PANEL_PROFILE.open(newline="", encoding="utf-8") as source:
        return [row["date"] for row in csv.DictReader(source)]


def fetch(start_date: str, end_date: str) -> dict:
    query = urllib.parse.urlencode(
        {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(HOURLY_FIELDS),
            "timezone": TIMEZONE,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "models": "era5_seamless",
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "uber-driver-market-study/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def aligned_rows(payload: dict) -> list[dict[str, float | int | str]]:
    hourly = payload["hourly"]
    output = []
    for index, timestamp in enumerate(hourly["time"]):
        row: dict[str, float | int | str] = {"timestamp_local": timestamp}
        for field in HOURLY_FIELDS:
            row[field] = hourly[field][index]
        output.append(row)
    return output


def aggregate(date: str, rows: list[dict[str, float | int | str]]) -> dict[str, object]:
    selected = []
    for row in rows:
        timestamp = datetime.fromisoformat(str(row["timestamp_local"]))
        if timestamp.date().isoformat() == date and 16 <= timestamp.hour <= 23:
            selected.append(row)
    if len(selected) != 8:
        raise RuntimeError(f"Expected 8 hourly observations for {date}; found {len(selected)}")

    temperatures = [float(row["temperature_2m"]) for row in selected]
    apparent = [float(row["apparent_temperature"]) for row in selected]
    precipitation = [float(row["precipitation"]) for row in selected]
    gusts = [float(row["wind_gusts_10m"]) for row in selected]
    codes = [int(row["weather_code"]) for row in selected]
    return {
        "date": date,
        "window_local": "16:00-23:59",
        "mean_temperature_f": round(statistics.mean(temperatures), 2),
        "max_apparent_temperature_f": round(max(apparent), 2),
        "precipitation_inches": round(sum(precipitation), 3),
        "precipitation_hours": sum(value > 0 for value in precipitation),
        "max_weather_code": max(codes),
        "max_wind_gust_mph": round(max(gusts), 2),
        "weather_stress": int(
            sum(precipitation) >= 0.10
            or max(codes) >= 80
            or max(apparent) >= 95
            or max(gusts) >= 35
        ),
        "source": SOURCE_URL,
    }


def main() -> None:
    dates = load_dates()
    payload = fetch(min(dates), max(dates))
    hourly = aligned_rows(payload)
    output_rows = [aggregate(date, hourly) for date in dates]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)
    stressed = sum(int(row["weather_stress"]) for row in output_rows)
    print(f"Wrote {OUTPUT} with {len(output_rows)} dates; {stressed} weather-stress dates.")


if __name__ == "__main__":
    main()
