"""Extract event and normal-rate pregame slices for the NYC premium test."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


LOCAL_DEPS = Path(".deps").resolve()
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import duckdb  # noqa: E402


SOURCE = "https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2025-04.parquet"
DATES = Path("config/nyc_yankee_premium_dates.csv")
ZONES = Path("config/nyc_yankee_stadium_zones.csv")
OUTPUT = Path("data/cache/nyc_yankee_event_premium_2025-04.csv")
EXTENSIONS = Path(".duckdb/extensions").resolve()


def values(path: Path, field: str) -> list[str]:
    with path.open(newline="", encoding="utf-8") as source:
        return [row[field] for row in csv.DictReader(source)]


def main() -> None:
    dates = values(DATES, "date")
    zones = [int(value) for value in values(ZONES, "location_id")]
    date_sql = ", ".join(f"DATE '{value}'" for value in dates)
    zone_sql = ", ".join(str(value) for value in zones)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EXTENSIONS.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect()
    connection.execute(f"SET extension_directory='{EXTENSIONS.as_posix()}'")
    connection.execute("LOAD httpfs")
    query = f"""
        SELECT
            hvfhs_license_num,
            request_datetime,
            on_scene_datetime,
            pickup_datetime,
            dropoff_datetime,
            PULocationID AS pickup_location_id,
            DOLocationID AS dropoff_location_id,
            trip_miles,
            trip_time,
            base_passenger_fare,
            tips,
            driver_pay
        FROM read_parquet('{SOURCE}')
        WHERE CAST(request_datetime AS DATE) IN ({date_sql})
          AND PULocationID IN ({zone_sql})
          AND CAST(request_datetime AS TIME) >= TIME '17:05:00'
          AND CAST(request_datetime AS TIME) < TIME '19:05:00'
        ORDER BY request_datetime, pickup_location_id
    """
    output = OUTPUT.resolve().as_posix().replace("'", "''")
    connection.execute(f"COPY ({query}) TO '{output}' (HEADER, DELIMITER ',')")
    count = connection.execute(f"SELECT count(*) FROM read_csv_auto('{output}')").fetchone()[0]
    print(f"Cached {count:,} NYC pregame trips at {OUTPUT}.")


if __name__ == "__main__":
    main()
