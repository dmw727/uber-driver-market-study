"""Derive deterministic community-area rings around Lake View from city boundaries."""

from __future__ import annotations

import csv
import json
import urllib.request
from collections import deque
from pathlib import Path

import geopandas as gpd


BOUNDARY_URL = "https://data.cityofchicago.org/resource/igwz-8jzy.geojson?$limit=100"
CORE_AREA = "6"
MAX_RING = 2
OUTPUT = Path("config/wrigley_spatial_rings.csv")


def fetch_geojson() -> dict:
    request = urllib.request.Request(
        BOUNDARY_URL,
        headers={"User-Agent": "uber-driver-market-study/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def property_value(properties: dict, candidates: tuple[str, ...]) -> str:
    for key in candidates:
        if properties.get(key) not in (None, ""):
            return str(properties[key])
    raise RuntimeError(f"Expected one of {candidates}; found {sorted(properties)}")


def main() -> None:
    payload = fetch_geojson()
    boundaries = gpd.GeoDataFrame.from_features(payload["features"], crs="EPSG:4326")
    boundaries = boundaries.to_crs("EPSG:3435")
    features: dict[str, dict] = {}
    names: dict[str, str] = {}
    geometries = {}
    for _, boundary in boundaries.iterrows():
        properties = boundary.to_dict()
        area = property_value(properties, ("area_numbe", "area_num_1", "area_number"))
        area = str(int(float(area)))
        features[area] = properties
        names[area] = property_value(properties, ("community", "community_area", "name"))
        geometries[area] = boundary.geometry

    adjacency = {area: set() for area in features}
    areas = sorted(features, key=int)
    for index, area in enumerate(areas):
        for other in areas[index + 1 :]:
            shared_boundary_feet = geometries[area].boundary.intersection(
                geometries[other].boundary
            ).length
            if shared_boundary_feet >= 10:
                adjacency[area].add(other)
                adjacency[other].add(area)

    distance = {CORE_AREA: 0}
    queue = deque([CORE_AREA])
    while queue:
        area = queue.popleft()
        if distance[area] >= MAX_RING:
            continue
        for neighbor in adjacency[area]:
            if neighbor not in distance:
                distance[neighbor] = distance[area] + 1
                queue.append(neighbor)

    rows = []
    labels = {0: "core", 1: "inner_ring", 2: "outer_ring"}
    for area, ring_distance in sorted(distance.items(), key=lambda item: (item[1], int(item[0]))):
        rows.append(
            {
                "community_area": area,
                "community_name": names[area],
                "ring_distance": ring_distance,
                "zone": labels[ring_distance],
                "boundary_source": BOUNDARY_URL,
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT} with {len(rows)} community areas.")
    for row in rows:
        print(f"  {row['zone']}: {row['community_area']} {row['community_name']}")


if __name__ == "__main__":
    main()
