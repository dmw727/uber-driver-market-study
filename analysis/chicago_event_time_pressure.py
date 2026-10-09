"""Compare event-night demand and occupied-vehicle pressure by clock time."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BINS = Path("data/derived/chicago_monday_panel_15min.csv")
VEHICLES = Path("data/derived/chicago_monday_panel_engaged_vehicle_bounds.csv")
WEATHER = Path("data/derived/chicago_monday_panel_weather.csv")
MANIFEST = Path("config/chicago_monday_panel_dates.csv")
OUTPUT = Path("data/derived/chicago_event_time_pressure.csv")
PHASE_OUTPUT = Path("data/derived/chicago_event_phase_pressure.csv")
REPORT = Path("docs/CHICAGO_EVENT_TIME_PRESSURE.md")
CHICAGO_TZ = ZoneInfo("America/Chicago")
PHASES = {
    "pregame_2h": (-120, 0),
    "game_first_2h": (0, 120),
    "game_late_post_2h": (120, 240),
    "extended_postgame": (240, 360),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def main() -> None:
    weather = {row["date"]: row for row in read_rows(WEATHER)}
    manifest = {row["date"]: row for row in read_rows(MANIFEST)}
    clean_dates = {
        date for date, row in weather.items() if int(row["weather_stress"]) == 0
    }
    bin_rows = read_rows(BINS)
    vehicle_rows = read_rows(VEHICLES)
    vehicle_index = {
        (row["date"], row["time_local"]): row
        for row in vehicle_rows
        if row["coverage_status"] == "post_p99_warmup"
    }

    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for row in bin_rows:
        if row["date"] not in clean_dates:
            continue
        vehicle = vehicle_index.get((row["date"], row["time_local"]))
        if vehicle is None:
            continue
        grouped[(row["group"], row["time_local"])].append(
            {
                "pickups": float(row["pickup_trips"]),
                "dropoffs": float(row["dropoff_trips"]),
                "unique": float(row["unique_trips"]),
                "engaged": float(vehicle["engaged_vehicles_bin_midpoint"]),
                "pickup_pressure": float(
                    vehicle["pickups_per_engaged_vehicle_midpoint"] or 0
                ),
            }
        )

    output_rows = []
    times = sorted({time for _, time in grouped})
    for time in times:
        events = grouped.get(("event", time), [])
        controls = grouped.get(("control", time), [])
        if not events or not controls:
            continue
        row: dict[str, object] = {
            "time_local": time,
            "event_dates": len(events),
            "control_dates": len(controls),
        }
        for metric in ("pickups", "dropoffs", "unique", "engaged", "pickup_pressure"):
            event_value = median([item[metric] for item in events])
            control_value = median([item[metric] for item in controls])
            row[f"event_median_{metric}"] = round(event_value, 3)
            row[f"control_median_{metric}"] = round(control_value, 3)
            row[f"{metric}_difference"] = round(event_value - control_value, 3)
            row[f"{metric}_relative_difference"] = (
                round(event_value / control_value - 1, 4) if control_value else ""
            )
        output_rows.append(row)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)

    control_baseline = {
        row["time_local"]: row for row in output_rows
    }
    phase_by_date: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"pickups": 0.0, "dropoffs": 0.0, "engaged": 0.0, "bins": 0.0}
    )
    for row in bin_rows:
        if row["group"] != "event" or row["date"] not in clean_dates:
            continue
        game_start_value = manifest[row["date"]]["game_start_utc"]
        if not game_start_value:
            continue
        game_start = datetime.fromisoformat(game_start_value.replace("Z", "+00:00")).astimezone(CHICAGO_TZ)
        timestamp = datetime.fromisoformat(f"{row['date']}T{row['time_local']}").replace(
            tzinfo=CHICAGO_TZ
        )
        relative_minutes = (timestamp - game_start).total_seconds() / 60
        phase = next(
            (
                name
                for name, (start, end) in PHASES.items()
                if start <= relative_minutes < end
            ),
            None,
        )
        baseline = control_baseline.get(row["time_local"])
        vehicle = vehicle_index.get((row["date"], row["time_local"]))
        if phase is None or baseline is None or vehicle is None:
            continue
        values = phase_by_date[(row["date"], phase)]
        values["pickups"] += float(row["pickup_trips"]) - float(
            baseline["control_median_pickups"]
        )
        values["dropoffs"] += float(row["dropoff_trips"]) - float(
            baseline["control_median_dropoffs"]
        )
        values["engaged"] += float(vehicle["engaged_vehicles_bin_midpoint"]) - float(
            baseline["control_median_engaged"]
        )
        values["bins"] += 1

    phase_rows = []
    for phase in PHASES:
        values = [
            metrics
            for (date_key, phase_key), metrics in phase_by_date.items()
            if phase_key == phase
        ]
        if not values:
            continue
        phase_rows.append(
            {
                "phase": phase,
                "event_dates": len(values),
                "median_excess_pickups": round(median([row["pickups"] for row in values]), 1),
                "median_excess_dropoffs": round(median([row["dropoffs"] for row in values]), 1),
                "median_excess_engaged_vehicle_bin_equivalents": round(
                    median([row["engaged"] for row in values]), 1
                ),
                "median_observed_bins": round(median([row["bins"] for row in values]), 1),
            }
        )
    with PHASE_OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=phase_rows[0].keys())
        writer.writeheader()
        writer.writerows(phase_rows)

    pickup_peak = max(output_rows, key=lambda row: float(row["pickups_difference"]))
    dropoff_peak = max(output_rows, key=lambda row: float(row["dropoffs_difference"]))
    engaged_peak = max(output_rows, key=lambda row: float(row["engaged_difference"]))
    pressure_peak = max(
        output_rows, key=lambda row: float(row["pickup_pressure_relative_difference"])
    )
    report = [
        "# Chicago Event-Time Vehicle Pressure",
        "",
        "## What this measures",
        "",
        "This analysis compares median 15-minute activity on non-weather-stress event Mondays with non-weather-stress comparison Mondays. Engaged vehicles are pickup-cohort equivalents inferred from reported trip duration, not a count of all drivers online.",
        "",
        "## Peak differences",
        "",
        f"- The largest excess in drop-offs occurs at {dropoff_peak['time_local']}: {float(dropoff_peak['dropoffs_difference']):,.0f} more drop-offs than the comparison median ({float(dropoff_peak['dropoffs_relative_difference']):.1%}).",
        f"- The largest excess in pickups occurs at {pickup_peak['time_local']}: {float(pickup_peak['pickups_difference']):,.0f} more pickups ({float(pickup_peak['pickups_relative_difference']):.1%}).",
        f"- Pickup-cohort engaged vehicles peak above comparison at {engaged_peak['time_local']}: {float(engaged_peak['engaged_difference']):,.1f} additional occupied-vehicle equivalents ({float(engaged_peak['engaged_relative_difference']):.1%}).",
        f"- The largest relative pickup pressure occurs at {pressure_peak['time_local']}: {float(pressure_peak['pickup_pressure_relative_difference']):.1%} above the comparison median.",
        "",
        "## Interpretation",
        "",
        "A pregame drop-off excess followed by a later pickup excess supports an event-shaped demand mechanism rather than a uniform all-evening increase. Elevated engaged-vehicle equivalents indicate more observed vehicles carrying passengers associated with Community Area 6, but the public data cannot determine idle supply, unfulfilled requests, surge multipliers, or exact driver availability.",
        "",
        "## First-pitch-aligned phases",
        "",
        "Each value below is the median across clean-weather event dates of the summed difference from the clean-control clock-time median. Engaged-vehicle values are sums of 15-minute vehicle equivalents and should be read as occupied capacity over the phase, not distinct drivers.",
        "",
        "| Phase | Event dates | Excess pickups | Excess drop-offs | Excess occupied-vehicle bin equivalents |",
        "|---|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['phase']} | {row['event_dates']} | {row['median_excess_pickups']:,.1f} | "
        f"{row['median_excess_dropoffs']:,.1f} | {row['median_excess_engaged_vehicle_bin_equivalents']:,.1f} |"
        for row in phase_rows
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(output_rows)} clock-time bins.")
    print(f"Wrote {PHASE_OUTPUT} with {len(phase_rows)} event phases.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
