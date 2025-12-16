from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def get_paths() -> tuple[Path, Path, Path, Path]:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    population_path = data_dir / "population_grid.geojson"
    isochrones_path = data_dir / "isochrones" / "parks_isochrones_15min.geojson"
    output_path = data_dir / "accessibility_cells_15min.geojson"

    return data_dir, population_path, isochrones_path, output_path


def main() -> None:
    data_dir, population_path, isochrones_path, output_path = get_paths()

    print(f"Data dir: {data_dir}")
    print(f"Population: {population_path}")
    print(f"Isochrones: {isochrones_path}")

    if not population_path.exists():
        raise FileNotFoundError(f"Population grid not found at {population_path}")
    if not isochrones_path.exists():
        raise FileNotFoundError(f"Isochrones file not found at {isochrones_path}")

    # Load data
    pop_gdf = gpd.read_file(population_path)
    iso_gdf = gpd.read_file(isochrones_path)

    print(f"Loaded {len(pop_gdf)} population cells")
    print(f"Loaded {len(iso_gdf)} park isochrones")

    # Union all isochrones into a single geometry
    print("\n[1] Building union of all isochrones…")
    iso_union = iso_gdf.unary_union

    # For each cell, check if its centroid is inside the union
    print("[2] Checking accessibility for each cell…")
    accessible_flags = []
    for geom in pop_gdf.geometry:
        centroid = geom.centroid
        accessible_flags.append(centroid.within(iso_union))

    pop_gdf["within_15min"] = accessible_flags

    # Compute accessibility numbers
    pop_gdf["total_pop"] = pop_gdf["population"]
    pop_gdf["pop_within_15"] = pop_gdf["population"].where(
        pop_gdf["within_15min"], 0
    )

    # Per cell, score is either 0 or 100, because we're treating it as
    # fully covered or not covered at all (based on centroid).
    pop_gdf["accessibility_score"] = (
        100.0 * pop_gdf["pop_within_15"] / pop_gdf["total_pop"]
    )

    pop_gdf.to_file(output_path, driver="GeoJSON")

    print("\n✅ DONE: Saved cell-level accessibility layer to:")
    print(f"   {output_path}")


if __name__ == "__main__":
    main()
