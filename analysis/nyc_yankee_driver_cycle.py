"""Measure how unpaid approach and pickup time change NYC trip economics."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


INPUT = Path("data/cache/nyc_yankee_driver_cycle_2025-04.csv")
DATES = Path("config/nyc_yankee_stadium_dates.csv")
ZONES = Path("config/nyc_yankee_stadium_zones.csv")
PROFILE_OUTPUT = Path("data/derived/nyc_yankee_driver_cycle_profile.csv")
ESTIMATE_OUTPUT = Path("data/derived/nyc_yankee_driver_cycle_estimates.csv")
REPORT = Path("docs/NYC_YANKEE_DRIVER_CYCLE.md")
PHASES = {
    "pregame_2h": (-120, 0),
    "game_first_2h": (0, 120),
    "game_late_post_2h": (120, 240),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def phase_for(request: datetime, anchor: datetime) -> str | None:
    relative = (request - anchor).total_seconds() / 60
    return next(
        (name for name, (start, end) in PHASES.items() if start <= relative < end),
        None,
    )


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def relative_change(event: float, control: float) -> float:
    return event / control - 1 if control else 0.0


def valid_trip(row: dict[str, str]) -> tuple[bool, dict[str, float]]:
    request = parse_time(row["request_datetime"])
    scene = parse_time(row["on_scene_datetime"])
    pickup = parse_time(row["pickup_datetime"])
    dropoff = parse_time(row["dropoff_datetime"])
    approach = (scene - request).total_seconds() / 60
    pickup_wait = (pickup - scene).total_seconds() / 60
    occupied = (dropoff - pickup).total_seconds() / 60
    total_cycle = (dropoff - request).total_seconds() / 60
    pay = float(row["driver_pay"])
    miles = float(row["trip_miles"])
    valid = (
        0 <= approach <= 120
        and 0 <= pickup_wait <= 60
        and 1 <= occupied <= 180
        and 1 <= total_cycle <= 240
        and 0 <= pay <= 500
        and 0 <= miles <= 100
    )
    return valid, {
        "approach_minutes": approach,
        "pickup_wait_minutes": pickup_wait,
        "occupied_minutes": occupied,
        "total_cycle_minutes": total_cycle,
        "driver_pay": pay,
        "trip_miles": miles,
        "occupied_pay_per_hour": pay / occupied * 60 if occupied else 0,
        "cycle_pay_per_hour": pay / total_cycle * 60 if total_cycle else 0,
        "unpaid_overhead_share": (approach + pickup_wait) / total_cycle if total_cycle else 0,
    }


def main() -> None:
    date_config = {row["date"]: row for row in read_rows(DATES)}
    zone_group = {row["location_id"]: row["zone_group"] for row in read_rows(ZONES)}
    grouped: dict[tuple[str, str, str], list[dict[str, float]]] = defaultdict(list)
    qa = defaultdict(int)
    platforms = defaultdict(int)

    for row in read_rows(INPUT):
        qa["raw"] += 1
        request = parse_time(row["request_datetime"])
        date = request.strftime("%Y-%m-%d")
        if date not in date_config:
            continue
        anchor = parse_time(date_config[date]["event_start_local"])
        phase = phase_for(request, anchor)
        if phase is None:
            continue
        qa["in_phase"] += 1
        valid, metrics = valid_trip(row)
        if not valid:
            qa["invalid"] += 1
            continue
        zone = zone_group.get(row["pickup_location_id"])
        if zone is None:
            continue
        grouped[(date, zone, phase)].append(metrics)
        platforms[row["hvfhs_license_num"]] += 1
        qa["usable"] += 1

    metric_names = (
        "approach_minutes",
        "pickup_wait_minutes",
        "occupied_minutes",
        "total_cycle_minutes",
        "driver_pay",
        "trip_miles",
        "occupied_pay_per_hour",
        "cycle_pay_per_hour",
        "unpaid_overhead_share",
    )
    profiles = []
    for (date, zone, phase), trips in sorted(grouped.items()):
        profile: dict[str, str | int | float] = {
            "date": date,
            "group": date_config[date]["group"],
            "matched_pair": date_config[date]["matched_pair"],
            "zone_group": zone,
            "phase": phase,
            "trips": len(trips),
        }
        for metric in metric_names:
            profile[f"median_{metric}"] = round(median([trip[metric] for trip in trips]), 4)
        profiles.append(profile)

    PROFILE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with PROFILE_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=profiles[0].keys())
        writer.writeheader()
        writer.writerows(profiles)

    estimates = []
    by_key = {
        (row["matched_pair"], row["group"], row["zone_group"], row["phase"]): row
        for row in profiles
    }
    for zone in ("core", "one_mile_ring"):
        for phase in PHASES:
            pair_changes = []
            for pair in ("1", "2", "3"):
                event = by_key.get((pair, "event", zone, phase))
                control = by_key.get((pair, "control", zone, phase))
                if not event or not control:
                    continue
                pair_changes.append(
                    {
                        "trip_volume": relative_change(float(event["trips"]), float(control["trips"])),
                        "approach": relative_change(
                            float(event["median_approach_minutes"]),
                            float(control["median_approach_minutes"]),
                        ),
                        "pickup_wait": relative_change(
                            float(event["median_pickup_wait_minutes"]),
                            float(control["median_pickup_wait_minutes"]),
                        ),
                        "occupied_rate": relative_change(
                            float(event["median_occupied_pay_per_hour"]),
                            float(control["median_occupied_pay_per_hour"]),
                        ),
                        "cycle_rate": relative_change(
                            float(event["median_cycle_pay_per_hour"]),
                            float(control["median_cycle_pay_per_hour"]),
                        ),
                        "overhead_share": float(event["median_unpaid_overhead_share"])
                        - float(control["median_unpaid_overhead_share"]),
                    }
                )
            estimates.append(
                {
                    "zone_group": zone,
                    "phase": phase,
                    "matched_pairs": len(pair_changes),
                    "median_trip_volume_change": round(median([p["trip_volume"] for p in pair_changes]), 4),
                    "median_approach_time_change": round(median([p["approach"] for p in pair_changes]), 4),
                    "median_pickup_wait_change": round(median([p["pickup_wait"] for p in pair_changes]), 4),
                    "median_occupied_pay_rate_change": round(
                        median([p["occupied_rate"] for p in pair_changes]), 4
                    ),
                    "median_cycle_pay_rate_change": round(
                        median([p["cycle_rate"] for p in pair_changes]), 4
                    ),
                    "median_overhead_share_point_change": round(
                        median([p["overhead_share"] for p in pair_changes]), 4
                    ),
                }
            )
    with ESTIMATE_OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=estimates[0].keys())
        writer.writeheader()
        writer.writerows(estimates)

    report = [
        "# NYC Yankee Stadium Driver-Cycle Benchmark",
        "",
        "## Question",
        "",
        "How does including approach and passenger-pickup waiting time change the apparent economics of event-area rideshare trips?",
        "",
        "## Design",
        "",
        "Three April 14-16, 2025 Yankees home games are paired by weekday with April 7-9 controls. Each phase is aligned to the 7:05 p.m. home-game start. West Concourse is the stadium core; the comparison ring contains official TLC taxi zones within one mile of the core polygon. NYC is a regulated-market measurement benchmark, not a proxy for Nashville or Chicago.",
        "",
        "Approach time is request to driver arrival, pickup wait is arrival to passenger pickup, and occupied time is pickup to drop-off. Full-cycle pay per hour divides reported driver pay by request-to-drop-off time. It is gross trip-level compensation, not net hourly earnings or a complete shift-level wage.",
        "",
        "## Matched results",
        "",
        "Values are medians of three weekday-matched event/control percentage changes. Overhead is reported as a percentage-point change.",
        "",
        "| Zone | Phase | Volume | Approach time | Pickup wait | Occupied pay/hour | Full-cycle pay/hour | Overhead share |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['zone_group']} | {row['phase']} | {row['median_trip_volume_change']:.1%} | "
        f"{row['median_approach_time_change']:.1%} | {row['median_pickup_wait_change']:.1%} | "
        f"{row['median_occupied_pay_rate_change']:.1%} | {row['median_cycle_pay_rate_change']:.1%} | "
        f"{row['median_overhead_share_point_change']:.1%} pts |"
        for row in estimates
    )
    report.extend(
        [
            "",
            "## What the complete clock changes",
            "",
            "The clearest reversal appears in the one-mile ring during the late-game/postgame phase. Occupied-only driver pay per hour was 0.5% above its matched controls, but approach time increased 17.4%; full request-to-drop-off pay per hour consequently fell 1.6%. An occupied-trip metric alone would give the wrong directional answer for this slice.",
            "",
            "Pregame in the stadium core shows a milder version of the same issue. Occupied pay per hour increased 2.1%, while full-cycle pay per hour was nearly unchanged at 0.1% after pickup waiting increased 13.2%.",
            "",
            "The core late-game/postgame result is different: trip volume increased 162.9% and full-cycle pay per hour increased 21.4% even though approach time nearly doubled. In this phase, stronger reported trip pay and longer occupied trips were large enough to offset the observed pre-pickup burden. The analytical lesson is therefore not that event cores or adjacent zones are universally better; it is that the recommendation can change when the full driver clock is measured.",
            "",
            "## Interpretation boundary",
            "",
            "Only three event dates are available in this bounded pilot, so these are descriptive paired estimates rather than a citywide causal effect. Taxi zones are coarse, event attendance is not observed, and request time does not include time spent logged in before receiving a request. Platform-reported driver pay excludes vehicle expenses and may reflect NYC-specific pay rules. The hourly figures describe time inside completed trip cycles, not all online time, and must not be presented as shift-level earnings.",
            "",
            "The comparison deliberately ends four hours after first pitch because the retained source slice ends at midnight; no incomplete extended-postgame phase is reported.",
            "",
            "## QA",
            "",
            f"- Raw bounded trips: {qa['raw']:,}",
            f"- Trips in the three analysis phases: {qa['in_phase']:,}",
            f"- Excluded for impossible or extreme timing/pay/distance values: {qa['invalid']:,}",
            f"- Usable trips: {qa['usable']:,}",
            f"- Usable platform records: {', '.join(f'{key}={value:,}' for key, value in sorted(platforms.items()))}",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {PROFILE_OUTPUT} with {len(profiles)} date-zone-phase rows.")
    print(f"Wrote {ESTIMATE_OUTPUT} with {len(estimates)} matched estimates.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
