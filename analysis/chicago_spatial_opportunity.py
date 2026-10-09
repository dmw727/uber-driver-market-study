"""Test whether event-adjacent zones offer lower-friction operating opportunity."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


CACHE_DIR = Path("data/cache/spatial_panel")
RINGS = Path("config/wrigley_spatial_rings.csv")
MANIFEST = Path("config/chicago_monday_panel_dates.csv")
WEATHER = Path("data/derived/chicago_monday_panel_weather.csv")
PROFILE_OUTPUT = Path("data/derived/chicago_spatial_zone_date_profile.csv")
ESTIMATE_OUTPUT = Path("data/derived/chicago_spatial_opportunity_estimates.csv")
PHASE_OUTPUT = Path("data/derived/chicago_spatial_event_phases.csv")
REPORT = Path("docs/CHICAGO_TANGENTIAL_STRATEGY.md")
CHICAGO_TZ = ZoneInfo("America/Chicago")
MONETARY_EXCLUSIONS = {"2026-08-31"}
PHASES = {
    "pregame_2h": (-120, 0),
    "game_first_2h": (0, 120),
    "game_late_post_2h": (120, 240),
    "extended_postgame": (240, 360),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def number(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value.replace("$", "").replace(",", "").strip())


def med(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def ratio_change(event: float, control: float) -> float | str:
    return round(event / control - 1, 4) if control else ""


def main() -> None:
    ring_rows = read_rows(RINGS)
    area_zone = {row["community_area"]: row["zone"] for row in ring_rows}
    area_count = defaultdict(int)
    for row in ring_rows:
        area_count[row["zone"]] += 1
    manifest = {row["date"]: row for row in read_rows(MANIFEST)}
    weather = {row["date"]: row for row in read_rows(WEATHER)}

    profiles = []
    clock_date: dict[tuple[str, str, str], dict[str, list[float] | int]] = defaultdict(
        lambda: {
            "pickups": 0,
            "minutes_per_mile": [],
            "fare_per_minute": [],
        }
    )
    phase_date: dict[tuple[str, str, str], dict[str, list[float] | int]] = defaultdict(
        lambda: {
            "pickups": 0,
            "minutes_per_mile": [],
            "fare_per_minute": [],
            "clock_times": set(),
        }
    )
    for date_key, details in manifest.items():
        path = CACHE_DIR / f"chicago_tnp_rings_{date_key}_1600_2359.csv"
        if not path.exists():
            continue
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        game_start = None
        if details["game_start_utc"]:
            game_start = datetime.fromisoformat(
                details["game_start_utc"].replace("Z", "+00:00")
            ).astimezone(CHICAGO_TZ)
        for trip in read_rows(path):
            zone = area_zone.get(trip.get("pickup_community_area", ""))
            if zone is None:
                continue
            grouped[zone].append(trip)
            timestamp = datetime.strptime(
                trip["trip_start_timestamp"], "%m/%d/%Y %I:%M:%S %p"
            ).replace(tzinfo=CHICAGO_TZ)
            clock_time = timestamp.strftime("%H:%M")
            seconds = number(trip.get("trip_seconds"))
            miles = number(trip.get("trip_miles"))
            fare = number(trip.get("fare"))
            clock_values = clock_date[(date_key, zone, clock_time)]
            clock_values["pickups"] = int(clock_values["pickups"]) + 1
            if seconds and miles and miles > 0:
                clock_values["minutes_per_mile"].append(seconds / 60 / miles)
            if (
                date_key not in MONETARY_EXCLUSIONS
                and seconds
                and fare is not None
                and seconds > 0
            ):
                clock_values["fare_per_minute"].append(fare / (seconds / 60))
            if game_start is None:
                continue
            relative_minutes = (timestamp - game_start).total_seconds() / 60
            phase = next(
                (
                    name
                    for name, (start, end) in PHASES.items()
                    if start <= relative_minutes < end
                ),
                None,
            )
            if phase is None:
                continue
            values = phase_date[(date_key, zone, phase)]
            values["pickups"] = int(values["pickups"]) + 1
            values["clock_times"].add(clock_time)
            if seconds and miles and miles > 0:
                values["minutes_per_mile"].append(seconds / 60 / miles)
            if (
                date_key not in MONETARY_EXCLUSIONS
                and seconds
                and fare is not None
                and seconds > 0
            ):
                values["fare_per_minute"].append(fare / (seconds / 60))

        for zone in ("core", "inner_ring", "outer_ring"):
            trips = grouped.get(zone, [])
            seconds = [value for trip in trips if (value := number(trip.get("trip_seconds"))) is not None]
            miles = [value for trip in trips if (value := number(trip.get("trip_miles"))) is not None]
            fares = [
                value
                for trip in trips
                if date_key not in MONETARY_EXCLUSIONS
                and (value := number(trip.get("fare"))) is not None
            ]
            minutes_per_mile = [
                number(trip["trip_seconds"]) / 60 / number(trip["trip_miles"])
                for trip in trips
                if number(trip.get("trip_seconds")) is not None
                and number(trip.get("trip_miles")) not in (None, 0)
            ]
            fare_per_minute = [
                number(trip["fare"]) / (number(trip["trip_seconds"]) / 60)
                for trip in trips
                if date_key not in MONETARY_EXCLUSIONS
                and number(trip.get("fare")) is not None
                and number(trip.get("trip_seconds")) not in (None, 0)
            ]
            profiles.append(
                {
                    "date": date_key,
                    "group": details["group"],
                    "weather_stress": weather[date_key]["weather_stress"],
                    "zone": zone,
                    "community_areas": area_count[zone],
                    "pickup_trips": len(trips),
                    "pickups_per_area": round(len(trips) / area_count[zone], 2),
                    "median_trip_minutes": round(med([value / 60 for value in seconds]), 3),
                    "median_trip_miles": round(med(miles), 3),
                    "median_minutes_per_mile": round(med(minutes_per_mile), 3),
                    "median_fare": round(med(fares), 3) if fares else "",
                    "median_fare_per_minute": round(med(fare_per_minute), 4)
                    if fare_per_minute
                    else "",
                    "monetary_status": "excluded" if date_key in MONETARY_EXCLUSIONS else "usable",
                }
            )

    with PROFILE_OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=profiles[0].keys())
        writer.writeheader()
        writer.writerows(profiles)

    clean = [row for row in profiles if row["weather_stress"] == "0"]
    estimates = []
    for zone in ("core", "inner_ring", "outer_ring"):
        zone_rows = [row for row in clean if row["zone"] == zone]
        event = [row for row in zone_rows if row["group"] == "event"]
        control = [row for row in zone_rows if row["group"] == "control"]
        event_pickups = med([float(row["pickups_per_area"]) for row in event])
        control_pickups = med([float(row["pickups_per_area"]) for row in control])
        event_friction = med([float(row["median_minutes_per_mile"]) for row in event])
        control_friction = med([float(row["median_minutes_per_mile"]) for row in control])
        event_rate = med(
            [float(row["median_fare_per_minute"]) for row in event if row["median_fare_per_minute"] != ""]
        )
        control_rate = med(
            [float(row["median_fare_per_minute"]) for row in control if row["median_fare_per_minute"] != ""]
        )
        demand_uplift = event_pickups / control_pickups - 1
        friction_change = event_friction / control_friction - 1
        opportunity_change = (1 + demand_uplift) / (1 + friction_change) - 1
        estimates.append(
            {
                "zone": zone,
                "community_areas": area_count[zone],
                "clean_event_dates": len(event),
                "clean_control_dates": len(control),
                "event_median_pickups_per_area": round(event_pickups, 2),
                "control_median_pickups_per_area": round(control_pickups, 2),
                "pickup_demand_uplift": round(demand_uplift, 4),
                "event_median_minutes_per_mile": round(event_friction, 3),
                "control_median_minutes_per_mile": round(control_friction, 3),
                "congestion_friction_change": round(friction_change, 4),
                "event_median_fare_per_minute": round(event_rate, 4),
                "control_median_fare_per_minute": round(control_rate, 4),
                "occupied_fare_rate_change": ratio_change(event_rate, control_rate),
                "demand_to_friction_change": round(opportunity_change, 4),
            }
        )

    with ESTIMATE_OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=estimates[0].keys())
        writer.writeheader()
        writer.writerows(estimates)

    phase_rows = []
    clean_control_dates = [
        date_key
        for date_key, details in manifest.items()
        if details["group"] == "control"
        and date_key in weather
        and weather[date_key]["weather_stress"] == "0"
    ]
    for zone in ("core", "inner_ring", "outer_ring"):
        for phase in PHASES:
            values = [
                (date_key, metrics)
                for (date_key, zone_key, phase_key), metrics in phase_date.items()
                if zone_key == zone
                and phase_key == phase
                and weather[date_key]["weather_stress"] == "0"
            ]
            if not values:
                continue
            comparisons = []
            for date_key, event_values in values:
                times = sorted(event_values["clock_times"])
                control_pickups = []
                control_friction = []
                control_fare_rate = []
                for control_date in clean_control_dates:
                    clock_values = [
                        clock_date[(control_date, zone, time)] for time in times
                    ]
                    control_pickups.append(
                        sum(int(value["pickups"]) for value in clock_values)
                    )
                    friction_values = [
                        item
                        for value in clock_values
                        for item in value["minutes_per_mile"]
                    ]
                    fare_values = [
                        item
                        for value in clock_values
                        for item in value["fare_per_minute"]
                    ]
                    control_friction.append(med(friction_values))
                    if fare_values:
                        control_fare_rate.append(med(fare_values))
                event_pickups = int(event_values["pickups"])
                baseline_pickups = med(control_pickups)
                event_friction = med(event_values["minutes_per_mile"])
                baseline_friction = med(control_friction)
                event_fare_rate = med(event_values["fare_per_minute"])
                baseline_fare_rate = med(control_fare_rate)
                comparisons.append(
                    {
                        "pickup_uplift": event_pickups / baseline_pickups - 1
                        if baseline_pickups
                        else 0,
                        "friction_change": event_friction / baseline_friction - 1
                        if baseline_friction
                        else 0,
                        "fare_rate_change": event_fare_rate / baseline_fare_rate - 1
                        if baseline_fare_rate and event_fare_rate
                        else 0,
                    }
                )
            phase_rows.append(
                {
                    "zone": zone,
                    "phase": phase,
                    "event_dates": len(values),
                    "median_pickups_per_area": round(
                        med([int(value["pickups"]) / area_count[zone] for _, value in values]), 2
                    ),
                    "median_minutes_per_mile": round(
                        med([med(value["minutes_per_mile"]) for _, value in values]), 3
                    ),
                    "median_fare_per_minute": round(
                        med(
                            [
                                med(value["fare_per_minute"])
                                for _, value in values
                                if value["fare_per_minute"]
                            ]
                        ),
                        4,
                    ),
                    "clock_matched_pickup_uplift": round(
                        med([value["pickup_uplift"] for value in comparisons]), 4
                    ),
                    "clock_matched_friction_change": round(
                        med([value["friction_change"] for value in comparisons]), 4
                    ),
                    "clock_matched_fare_rate_change": round(
                        med([value["fare_rate_change"] for value in comparisons]), 4
                    ),
                    "clock_matched_demand_to_friction": round(
                        med(
                            [
                                (1 + value["pickup_uplift"])
                                / (1 + value["friction_change"])
                                - 1
                                for value in comparisons
                            ]
                        ),
                        4,
                    ),
                }
            )
    with PHASE_OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=phase_rows[0].keys())
        writer.writeheader()
        writer.writerows(phase_rows)

    best = max(estimates, key=lambda row: float(row["demand_to_friction_change"]))
    report = [
        "# Tangential Driving Strategy: Chicago Test",
        "",
        "## Question",
        "",
        "Do areas adjacent to Wrigley capture event-related pickup demand with less trip-time friction than the Lake View event core?",
        "",
        "## Clean-weather zone comparison",
        "",
        "Pickup demand is normalized per community area. Congestion friction is median occupied minutes per mile. The demand-to-friction measure divides relative pickup uplift by relative friction; it is an operational comparison, not driver profit.",
        "",
        "| Zone | Pickup uplift | Friction change | Occupied fare/min change | Demand-to-friction change |",
        "|---|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['zone']} | {float(row['pickup_demand_uplift']):.1%} | "
        f"{float(row['congestion_friction_change']):.1%} | "
        f"{float(row['occupied_fare_rate_change']):.1%} | "
        f"{float(row['demand_to_friction_change']):.1%} |"
        for row in estimates
    )
    report.extend(
        [
            "",
            "## Preliminary answer",
            "",
            f"The strongest demand-to-friction change appears in the **{best['zone']}** ({float(best['demand_to_friction_change']):.1%}). This result should be interpreted alongside the phase table before recommending a strategy, because a zone may be attractive only during a specific pregame or postgame interval.",
            "",
            "## Limits",
            "",
            "Fare is passenger fare, not driver pay. The data omit idle time, deadheading, acceptance rates, unfulfilled requests, surge multipliers, and exact routes. Community areas also differ internally and in size; per-area normalization is only a first control. August 31 remains in pickup counts but is excluded from every monetary metric.",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {PROFILE_OUTPUT} with {len(profiles)} date-zone rows.")
    print(f"Wrote {ESTIMATE_OUTPUT}.")
    print(f"Wrote {PHASE_OUTPUT}.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
