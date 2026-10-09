"""Build a deterministic Yankee Stadium taxi-zone core and one-mile ring."""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


SHAPEFILE = Path("data/metadata/nyc_taxi_zones/taxi_zones/taxi_zones.shp")
OUTPUT = Path("config/nyc_yankee_stadium_zones.csv")
STADIUM = Point(-73.9262, 40.8296)
RING_FEET = 5_280
SOURCE = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"


def main() -> None:
    zones = gpd.read_file(SHAPEFILE).to_crs(4326)
    core_matches = zones[zones.geometry.contains(STADIUM)]
    if len(core_matches) != 1:
        raise RuntimeError(f"Expected one stadium taxi zone, found {len(core_matches)}.")
    core_id = int(core_matches.iloc[0]["LocationID"])
    projected = zones.to_crs(2263)
    core_geometry = projected[projected["LocationID"] == core_id].geometry.iloc[0]
    projected["distance_to_core_feet"] = projected.geometry.distance(core_geometry)
    selected = projected[projected["distance_to_core_feet"] <= RING_FEET].copy()
    selected["zone_group"] = selected["LocationID"].apply(
        lambda value: "core" if int(value) == core_id else "one_mile_ring"
    )
    selected = selected.sort_values(["zone_group", "distance_to_core_feet", "LocationID"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=(
                "location_id",
                "borough",
                "zone",
                "zone_group",
                "distance_to_core_feet",
                "boundary_source",
            ),
        )
        writer.writeheader()
        for _, row in selected.iterrows():
            writer.writerow(
                {
                    "location_id": int(row["LocationID"]),
                    "borough": row["borough"],
                    "zone": row["zone"],
                    "zone_group": row["zone_group"],
                    "distance_to_core_feet": round(float(row["distance_to_core_feet"]), 1),
                    "boundary_source": SOURCE,
                }
            )
    print(f"Wrote {OUTPUT} with {len(selected)} zones; stadium core is {core_id}.")


if __name__ == "__main__":
    main()
