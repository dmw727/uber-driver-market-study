"""Validate Wrigley access and egress friction with arterial segment speeds."""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path


CACHE_DIR = Path("data/cache/traffic_tracker")
OUTPUT = Path("data/derived/chicago_april_traffic_validation.csv")
REPORT = Path("docs/CHICAGO_APRIL_TRAFFIC_VALIDATION.md")
EVENT_DATE = "2026-04-20"
CONTROL_DATES = ("2026-04-06", "2026-04-13", "2026-04-27")
WRIGLEY = (41.9484, -87.6553)
MIN_SUPPORT = 1
PHASES = {
    "pregame_2h": (16 * 60 + 40, 18 * 60 + 40),
    "game_first_2h": (18 * 60 + 40, 20 * 60 + 40),
    "game_late_post_2h": (20 * 60 + 40, 22 * 60 + 40),
    "extended_postgame": (22 * 60 + 40, 24 * 60),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def miles(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    lat_scale = 69.0
    lon_scale = 69.0 * math.cos(math.radians((a_lat + b_lat) / 2))
    return math.hypot((a_lat - b_lat) * lat_scale, (a_lon - b_lon) * lon_scale)


def phase_for(timestamp: datetime) -> str | None:
    minute = timestamp.hour * 60 + timestamp.minute
    return next((name for name, (start, end) in PHASES.items() if start <= minute < end), None)


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def clean_round(value: float, digits: int) -> float:
    rounded = round(value, digits)
    return 0.0 if rounded == 0 else rounded


def main() -> None:
    observations: dict[tuple[str, str, str], list[dict[str, float | str]]] = defaultdict(list)
    qa = defaultdict(int)
    for date in (*CONTROL_DATES, EVENT_DATE):
        path = CACHE_DIR / f"chicago_traffic_segments_{date}_1600_2359.csv"
        for row in read_rows(path):
            qa["raw"] += 1
            speed = float(row["speed"])
            support = max(int(float(row.get("bus_count") or 0)), int(float(row.get("message_count") or 0)))
            if speed <= 0 or support < MIN_SUPPORT:
                qa["excluded"] += 1
                continue
            timestamp = datetime.fromisoformat(row["time"])
            phase = phase_for(timestamp)
            if phase is None:
                continue
            start_distance = miles(
                float(row["start_latitude"]), float(row["start_longitude"]), *WRIGLEY
            )
            end_distance = miles(
                float(row["end_latitude"]), float(row["end_longitude"]), *WRIGLEY
            )
            midpoint_distance = (start_distance + end_distance) / 2
            if midpoint_distance > 5:
                continue
            movement = "inbound" if end_distance < start_distance else "outbound"
            band = "core_access" if midpoint_distance <= 1.5 else "approach_ring"
            clock = timestamp.strftime("%H:%M")
            observations[(date, row["segment_id"], clock)].append(
                {
                    "phase": phase,
                    "movement": movement,
                    "band": band,
                    "speed": speed,
                    "length": float(row["length"]),
                    "street": row["street"],
                }
            )
            qa["usable"] += 1

    matched: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for (date, segment_id, clock), event_rows in observations.items():
        if date != EVENT_DATE:
            continue
        event = event_rows[0]
        controls = [
            rows[0]
            for control_date in CONTROL_DATES
            if (rows := observations.get((control_date, segment_id, clock)))
        ]
        if len(controls) < 2:
            qa["unmatched_event"] += 1
            continue
        baseline_speed = median([float(row["speed"]) for row in controls])
        if baseline_speed <= 0:
            continue
        event_speed = float(event["speed"])
        length = float(event["length"])
        matched[(str(event["phase"]), f"{event['band']}_{event['movement']}")].append(
            {
                "speed_change": event_speed / baseline_speed - 1,
                "delay_minutes": length / event_speed * 60 - length / baseline_speed * 60,
                "event_speed": event_speed,
                "baseline_speed": baseline_speed,
            }
        )
        qa["matched"] += 1

    output_rows = []
    for (phase, corridor), values in sorted(matched.items()):
        output_rows.append(
            {
                "phase": phase,
                "corridor": corridor,
                "matched_segment_intervals": len(values),
                "median_event_speed_mph": round(median([v["event_speed"] for v in values]), 2),
                "median_control_speed_mph": round(median([v["baseline_speed"] for v in values]), 2),
                "median_speed_change": clean_round(median([v["speed_change"] for v in values]), 4),
                "mean_speed_change": clean_round(mean([v["speed_change"] for v in values]), 4),
                "median_delay_minutes_per_segment": clean_round(
                    median([v["delay_minutes"] for v in values]), 3
                ),
                "mean_delay_minutes_per_segment": clean_round(
                    mean([v["delay_minutes"] for v in values]), 3
                ),
                "share_slower_than_control": round(
                    sum(v["speed_change"] < 0 for v in values) / len(values), 4
                ),
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=output_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)

    report = [
        "# April Traffic-Speed Validation",
        "",
        "## Decision question",
        "",
        "Did road congestion around Wrigley create an access or egress penalty large enough to qualify the apparent event-core pickup opportunity?",
        "",
        "This is a Chicago transfer test of a strategy hypothesis developed from the author's Nashville Uber-driving experience. The author lived in the Chicago area but did not drive Uber there; the analysis does not treat local familiarity as Chicago rideshare operating experience.",
        "",
        "## Design",
        "",
        "April 20, 2026 arterial speeds are matched by segment and clock time to April 6, 13, and 27. A segment is inbound when its recorded direction ends closer to Wrigley Field and outbound when it ends farther away. Core-access segments have midpoints within 1.5 miles; approach-ring segments are 1.5 to 5 miles away.",
        "",
        "Invalid speeds and observations without bus/message support are excluded. Reported delay is the change in traversal time for one observed arterial segment, not a full pickup route.",
        "",
        "## Results",
        "",
        "Because speeds are integer-valued, median pairwise changes often equal zero. Mean pairwise change and the share of intervals running slower preserve the underlying variation.",
        "",
        "| Phase | Corridor | Matched intervals | Event mph | Control mph | Mean speed change | Mean delay/segment | Share slower |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    report.extend(
        f"| {row['phase']} | {row['corridor']} | {row['matched_segment_intervals']} | "
        f"{row['median_event_speed_mph']:.2f} | {row['median_control_speed_mph']:.2f} | "
        f"{row['mean_speed_change']:.1%} | {row['mean_delay_minutes_per_segment']:.2f} min | "
        f"{row['share_slower_than_control']:.1%} |"
        for row in output_rows
    )
    report.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This is a validation case study, not a season-wide causal estimate or evidence that Chicago and Nashville traffic behave alike. The archive ends April 30, leaving one Cubs home-game Monday and three April controls. Traffic Tracker covers selected arterials and derives estimates from CTA bus GPS traces; it does not observe dispatch-to-pickup time, side-street crawling, queue position, or the driver's actual route.",
            "",
            "The traffic results should therefore qualify the full-season occupied-trip findings rather than be merged into a precise driver-profit estimate.",
            "",
            "## QA",
            "",
            f"- Raw observations: {qa['raw']:,}",
            f"- Excluded invalid or unsupported observations: {qa['excluded']:,}",
            f"- Usable observations inside five miles: {qa['usable']:,}",
            f"- Matched event segment-intervals: {qa['matched']:,}",
            f"- Event observations lacking two controls: {qa['unmatched_event']:,}",
        ]
    )
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} with {len(output_rows)} phase-corridor rows.")
    print(f"Wrote {REPORT}.")


if __name__ == "__main__":
    main()
