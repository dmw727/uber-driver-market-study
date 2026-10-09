"""Estimate event-associated pay premium and throughput for spillover trips."""

from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Point


INPUT = Path("data/cache/nyc_yankee_event_premium_2025-04.csv")
DATES = Path("config/nyc_yankee_premium_dates.csv")
ZONES = Path("config/nyc_yankee_stadium_zones.csv")
SHAPEFILE = Path("data/metadata/nyc_taxi_zones/taxi_zones/taxi_zones.shp")
DATE_OUTPUT = Path("data/derived/nyc_surge_spillover_date_profile.csv")
ESTIMATE_OUTPUT = Path("data/derived/nyc_surge_spillover_estimates.csv")
REPORT = Path("docs/NYC_SURGE_SPILLOVER_STRATEGY.md")
STADIUM_LON_LAT = (-73.9262, 40.8296)
AWAY_MARGIN_FEET = 1_320
MIN_DATE_TRIPS = 20


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def valid_metrics(row: dict[str, str]) -> dict[str, float] | None:
    request = datetime.fromisoformat(row["request_datetime"])
    scene = datetime.fromisoformat(row["on_scene_datetime"])
    pickup = datetime.fromisoformat(row["pickup_datetime"])
    dropoff = datetime.fromisoformat(row["dropoff_datetime"])
    approach = (scene - request).total_seconds() / 60
    wait = (pickup - scene).total_seconds() / 60
    occupied = (dropoff - pickup).total_seconds() / 60
    cycle = (dropoff - request).total_seconds() / 60
    pay = float(row["driver_pay"])
    passenger_fare = float(row["base_passenger_fare"])
    miles = float(row["trip_miles"])
    if not (
        0 <= approach <= 120
        and 0 <= wait <= 60
        and 1 <= occupied <= 180
        and 1 <= cycle <= 240
        and 0 < pay <= 500
        and 0 < passenger_fare <= 1_000
        and 0 < miles <= 100
    ):
        return None
    return {
        "approach": approach,
        "wait": wait,
        "occupied": occupied,
        "cycle": cycle,
        "pay": pay,
        "passenger_fare": passenger_fare,
        "miles": miles,
        "cycle_pay_rate": pay / cycle * 60,
    }


def zone_distances() -> dict[int, float]:
    zones = gpd.read_file(SHAPEFILE).to_crs(4326)
    stadium = gpd.GeoSeries([Point(*STADIUM_LON_LAT)], crs=4326).to_crs(2263).iloc[0]
    projected = zones.to_crs(2263)
    return {
        int(row["LocationID"]): float(row.geometry.centroid.distance(stadium))
        for _, row in projected.iterrows()
    }


def strategy_for(
    pickup: int,
    dropoff: int,
    core: set[int],
    ring: set[int],
    distances: dict[int, float],
) -> str | None:
    if pickup in ring:
        if dropoff in core:
            return "stadium_bound"
        if dropoff in ring:
            return "spillover_local"
        if (
            pickup in distances
            and dropoff in distances
            and distances[dropoff] >= distances[pickup] + AWAY_MARGIN_FEET
        ):
            return "spillover_away"
        return None
    if pickup in core and dropoff not in core and dropoff in distances:
        return "core_departure"
    return None


def feature_schema(rows: list[dict[str, object]]) -> tuple[list[str], dict[str, list[str]]]:
    categories = {
        "platform": sorted({str(row["platform"]) for row in rows}),
        "pickup": sorted({str(row["pickup"]) for row in rows}),
        "strategy": sorted({str(row["strategy"]) for row in rows}),
        "weekday": sorted({str(row["weekday"]) for row in rows}),
        "slot": sorted({str(row["slot"]) for row in rows}),
    }
    names = ["intercept", "log_miles", "log_occupied", "log_approach", "log_wait"]
    for field, values in categories.items():
        names.extend(f"{field}={value}" for value in values[1:])
    return names, categories


def feature_vector(row: dict[str, object], categories: dict[str, list[str]]) -> list[float]:
    vector = [
        1.0,
        math.log1p(float(row["miles"])),
        math.log1p(float(row["occupied"])),
        math.log1p(float(row["approach"])),
        math.log1p(float(row["wait"])),
    ]
    for field, values in categories.items():
        vector.extend(float(str(row[field]) == value) for value in values[1:])
    return vector


def main() -> None:
    dates = {row["date"]: row for row in read_rows(DATES)}
    zone_rows = read_rows(ZONES)
    core = {int(row["location_id"]) for row in zone_rows if row["zone_group"] == "core"}
    ring = {int(row["location_id"]) for row in zone_rows if row["zone_group"] == "one_mile_ring"}
    distances = zone_distances()
    records: list[dict[str, object]] = []
    qa = Counter()

    for row in read_rows(INPUT):
        qa["raw"] += 1
        metrics = valid_metrics(row)
        if metrics is None:
            qa["invalid"] += 1
            continue
        pickup = int(row["pickup_location_id"])
        dropoff = int(row["dropoff_location_id"])
        strategy = strategy_for(pickup, dropoff, core, ring, distances)
        if strategy is None:
            qa["unclassified"] += 1
            continue
        request = datetime.fromisoformat(row["request_datetime"])
        date = request.strftime("%Y-%m-%d")
        if date not in dates:
            continue
        records.append(
            {
                **metrics,
                "date": date,
                "group": dates[date]["group"],
                "platform": row["hvfhs_license_num"],
                "pickup": str(pickup),
                "strategy": strategy,
                "weekday": request.strftime("%A"),
                "slot": f"{request.hour:02d}:{(request.minute // 15) * 15:02d}",
            }
        )
        qa["classified"] += 1

    controls = [row for row in records if row["group"] == "control"]
    _, categories = feature_schema(controls)
    x_control = np.asarray([feature_vector(row, categories) for row in controls], dtype=float)
    y_pay = np.log(np.asarray([float(row["pay"]) for row in controls], dtype=float))
    y_fare = np.log(
        np.asarray([float(row["passenger_fare"]) for row in controls], dtype=float)
    )
    pay_coefficients, _, _, _ = np.linalg.lstsq(x_control, y_pay, rcond=None)
    fare_coefficients, _, _, _ = np.linalg.lstsq(x_control, y_fare, rcond=None)
    pay_fitted = x_control @ pay_coefficients
    fare_fitted = x_control @ fare_coefficients
    pay_r_squared = 1 - float(np.sum((y_pay - pay_fitted) ** 2)) / float(
        np.sum((y_pay - np.mean(y_pay)) ** 2)
    )
    fare_r_squared = 1 - float(np.sum((y_fare - fare_fitted) ** 2)) / float(
        np.sum((y_fare - np.mean(y_fare)) ** 2)
    )

    for row in records:
        vector = feature_vector(row, categories)
        pay_prediction = float(np.dot(vector, pay_coefficients))
        fare_prediction = float(np.dot(vector, fare_coefficients))
        row["pay_ratio_to_normal"] = float(row["pay"]) / math.exp(pay_prediction)
        row["fare_ratio_to_normal"] = float(row["passenger_fare"]) / math.exp(
            fare_prediction
        )

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in records:
        grouped[(str(row["date"]), str(row["strategy"]))].append(row)

    profiles = []
    for (date, strategy), trips in sorted(grouped.items()):
        profiles.append(
            {
                "date": date,
                "group": dates[date]["group"],
                "strategy": strategy,
                "trips": len(trips),
                "median_pay_ratio_to_normal": round(
                    median([float(row["pay_ratio_to_normal"]) for row in trips]), 4
                ),
                "median_fare_ratio_to_normal": round(
                    median([float(row["fare_ratio_to_normal"]) for row in trips]), 4
                ),
                "median_driver_pay": round(median([float(row["pay"]) for row in trips]), 2),
                "median_cycle_minutes": round(median([float(row["cycle"]) for row in trips]), 3),
                "median_cycle_pay_rate": round(
                    median([float(row["cycle_pay_rate"]) for row in trips]), 2
                ),
                "two_hour_cycle_capacity": round(
                    120 / median([float(row["cycle"]) for row in trips]), 2
                ),
                "two_hour_gross_capacity_proxy": round(
                    2 * median([float(row["cycle_pay_rate"]) for row in trips]), 2
                ),
            }
        )
    DATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with DATE_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=profiles[0].keys())
        writer.writeheader()
        writer.writerows(profiles)

    strategies = ("stadium_bound", "spillover_local", "spillover_away", "core_departure")
    estimates = []
    for strategy in strategies:
        usable = [
            row for row in profiles if row["strategy"] == strategy and int(row["trips"]) >= MIN_DATE_TRIPS
        ]
        event = [row for row in usable if row["group"] == "event"]
        control = [row for row in usable if row["group"] == "control"]
        if not event or not control:
            continue
        event_ratio = median([float(row["median_pay_ratio_to_normal"]) for row in event])
        control_ratio = median([float(row["median_pay_ratio_to_normal"]) for row in control])
        event_fare_ratio = median(
            [float(row["median_fare_ratio_to_normal"]) for row in event]
        )
        control_fare_ratio = median(
            [float(row["median_fare_ratio_to_normal"]) for row in control]
        )
        estimates.append(
            {
                "strategy": strategy,
                "event_dates": len(event),
                "control_dates": len(control),
                "event_median_trips": round(median([float(row["trips"]) for row in event]), 1),
                "control_median_trips": round(median([float(row["trips"]) for row in control]), 1),
                "trip_volume_change": round(
                    median([float(row["trips"]) for row in event])
                    / median([float(row["trips"]) for row in control])
                    - 1,
                    4,
                ),
                "implied_event_pay_premium": round(event_ratio / control_ratio - 1, 4),
                "implied_event_passenger_fare_premium": round(
                    event_fare_ratio / control_fare_ratio - 1, 4
                ),
                "event_median_cycle_minutes": round(
                    median([float(row["median_cycle_minutes"]) for row in event]), 3
                ),
                "control_median_cycle_minutes": round(
                    median([float(row["median_cycle_minutes"]) for row in control]), 3
                ),
                "cycle_time_change": round(
                    median([float(row["median_cycle_minutes"]) for row in event])
                    / median([float(row["median_cycle_minutes"]) for row in control])
                    - 1,
                    4,
                ),
                "event_two_hour_cycle_capacity": round(
                    median([float(row["two_hour_cycle_capacity"]) for row in event]), 2
                ),
                "control_two_hour_cycle_capacity": round(
                    median([float(row["two_hour_cycle_capacity"]) for row in control]), 2
                ),
                "event_two_hour_gross_capacity_proxy": round(
                    median([float(row["two_hour_gross_capacity_proxy"]) for row in event]), 2
                ),
                "control_two_hour_gross_capacity_proxy": round(
                    median([float(row["two_hour_gross_capacity_proxy"]) for row in control]), 2
                ),
            }
        )
    with ESTIMATE_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=estimates[0].keys())
        writer.writeheader()
        writer.writerows(estimates)

    report = [
        "# NYC Surge-Spillover Strategy Test",
        "",
        "## Strategy question",
        "",
        "Can a driver capture event-associated compensation in the venue spillover area while choosing trips that move away from stadium traffic, thereby preserving more trip-completion capacity during the two-hour pregame window?",
        "",
        "## Design",
        "",
        "The April 14-16, 2025 Yankees home-game pregame windows are compared with nine Monday-Wednesday evenings when the Yankees were away. Normal passenger-fare and driver-pay models are trained only on controls and adjust for platform, pickup zone, weekday, 15-minute slot, miles, occupied time, approach time, pickup waiting, and trip-direction class. Each implied premium is the event actual-to-model ratio relative to the corresponding control ratio; neither is a platform-reported surge multiplier.",
        "",
        "Spillover-away trips begin in the one-mile ring, end outside the ring, and finish at least one-quarter mile farther from Yankee Stadium than the pickup-zone centroid. Stadium-bound trips begin in the ring and end in the stadium core.",
        "",
        "## Results",
        "",
        "| Strategy | Event trips | Volume change | Passenger-fare premium | Driver-pay premium | Cycle change | Event cycles / 2h | Gross capacity proxy / 2h |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['strategy']} | {row['event_median_trips']:.0f} | {row['trip_volume_change']:.1%} | "
        f"{row['implied_event_passenger_fare_premium']:.1%} | "
        f"{row['implied_event_pay_premium']:.1%} | {row['cycle_time_change']:.1%} | "
        f"{row['event_two_hour_cycle_capacity']:.2f} | ${row['event_two_hour_gross_capacity_proxy']:.2f} |"
        for row in estimates
    )
    report.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The fare and pay premiums are model-implied and event-associated; they do not reveal the app's surge multiplier. NYC's TLC minimum per-trip payment standard, based partly on time and mileage, can compress variation in reported driver pay. A near-zero driver-pay premium therefore cannot establish how the same strategy would perform in Nashville. Passenger base fare and reported driver pay are separate outcomes and should not be treated as interchangeable. Taxi-zone centroids approximate direction and do not reveal the exact route. Cycle capacity assumes back-to-back comparable completed trips and excludes idle time before the next request, repositioning after drop-off, expenses, cancellations, and the possibility that an away trip leaves the premium area. It is a throughput ceiling, not observed rides per driver.",
            "",
            "Control dates were screened for Yankees home games, not every possible local event or source of chaotic demand. Date-level control residuals in the companion CSV should be reviewed before treating the baseline as ordinary.",
            "",
            "## QA",
            "",
            f"- Raw pregame trips: {qa['raw']:,}",
            f"- Excluded invalid timing/pay/distance records: {qa['invalid']:,}",
            f"- Classified strategy trips: {qa['classified']:,}",
            f"- Other directional patterns not used: {qa['unclassified']:,}",
            f"- Normal-pay training trips: {len(controls):,}",
            f"- Control-model R-squared (log driver pay): {pay_r_squared:.3f}",
            f"- Control-model R-squared (log passenger base fare): {fare_r_squared:.3f}",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {DATE_OUTPUT} with {len(profiles)} date-strategy rows.")
    print(f"Wrote {ESTIMATE_OUTPUT} with {len(estimates)} strategy estimates.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
