from __future__ import annotations

from pathlib import Path
from typing import List

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon


CELL_SIZE_METERS = 500  # size of each grid cell


def get_paths() -> tuple[Path, Path, Path]:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    boundary_path = data_dir / "boundary.geojson"
    population_path = data_dir / "population_grid.geojson"
    return data_dir, boundary_path, population_path


def make_grid_over_boundary(boundary_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Create a regular square grid over the boundary in a projected CRS
    and clip it to the boundary shape.
    """
    # Work in meters: project to suitable UTM
    utm_crs = boundary_gdf.estimate_utm_crs()
    boundary_utm = boundary_gdf.to_crs(utm_crs)
    boundary_geom = boundary_utm.geometry.iloc[0]

    minx, miny, maxx, maxy = boundary_geom.bounds

    polygons: List[Polygon] = []

    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            poly = Polygon(
                [
                    (x, y),
                    (x + CELL_SIZE_METERS, y),
                    (x + CELL_SIZE_METERS, y + CELL_SIZE_METERS),
                    (x, y + CELL_SIZE_METERS),
                ]
            )
            polygons.append(poly)
            x += CELL_SIZE_METERS
        y += CELL_SIZE_METERS

    grid_gdf = gpd.GeoDataFrame({"geometry": polygons}, crs=utm_crs)

    # Clip grid to boundary
    grid_clipped = gpd.overlay(grid_gdf, boundary_utm, how="intersection")
    grid_clipped.reset_index(drop=True, inplace=True)

    # Reproject back to WGS84 (lat/lon) for consistency with everything else
    grid_clipped = grid_clipped.to_crs("EPSG:4326")

    return grid_clipped


def assign_synthetic_population(grid_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Assign a synthetic population value to each grid cell.

    For now, we just sample random values so we can test the pipeline.
    Later, you can replace this with real census data.
    """
    np.random.seed(42)

    # For example: random pop between 50 and 500 per cell
    pops = np.random.randint(50, 500, size=len(grid_gdf))
    grid_gdf["population"] = pops

    return grid_gdf


def main() -> None:
    data_dir, boundary_path, population_path = get_paths()

    print(f"Data dir: {data_dir}")
    print(f"Boundary path: {boundary_path}")

    if not boundary_path.exists():
        raise FileNotFoundError(f"Boundary file not found at {boundary_path}")

    boundary_gdf = gpd.read_file(boundary_path)
    print("Loaded boundary")

    print("\n[1] Building grid over boundary…")
    grid = make_grid_over_boundary(boundary_gdf)
    print(f"  Cells in grid (after clip): {len(grid)}")

    print("\n[2] Assigning synthetic population…")
    grid = assign_synthetic_population(grid)

    grid.to_file(population_path, driver="GeoJSON")
    print(f"\n✅ DONE: Saved population grid to:\n   {population_path}")


if __name__ == "__main__":
    main()
