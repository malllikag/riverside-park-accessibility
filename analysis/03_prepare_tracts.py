from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def get_paths():
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    census_dir = data_dir / "census_data"

    # Find the first .shp in data/census_data so you don't have to hardcode the name
    shp_files = list(census_dir.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No .shp files found in {census_dir}")
    if len(shp_files) > 1:
        raise RuntimeError(
            f"Multiple .shp files found in {census_dir}, "
            f"please keep only the census tracts shapefile or edit this script."
        )

    tracts_path = shp_files[0]
    boundary_path = data_dir / "boundary.geojson"
    out_path = data_dir / "riverside_tracts_with_population.geojson"

    return tracts_path, boundary_path, out_path


def main() -> None:
    tracts_path, boundary_path, out_path = get_paths()

    print(f"Tracts shapefile : {tracts_path}")
    print(f"City boundary    : {boundary_path}")

    if not tracts_path.exists():
        raise FileNotFoundError(f"Could not find tracts shapefile at {tracts_path}")
    if not boundary_path.exists():
        raise FileNotFoundError(f"Could not find boundary.geojson at {boundary_path}")

    # 1) Load tracts + city boundary
    print("\n[1] Loading tracts…")
    tracts = gpd.read_file(tracts_path)
    print(f"  Tracts loaded: {len(tracts)}")
    print("  Columns:", list(tracts.columns))

    print("\n[2] Loading city boundary…")
    boundary = gpd.read_file(boundary_path)
    print(f"  Boundary loaded: {len(boundary)} feature(s)")

    # 2) Align CRS (projection) for correct spatial operations
    if tracts.crs is None:
        raise ValueError("Tracts layer has no CRS; check the shapefile in QGIS/ArcGIS.")
    boundary = boundary.to_crs(tracts.crs)

    # 3) Clip tracts to the Riverside city boundary
    print("\n[3] Clipping tracts to city boundary…")
    tracts_clipped = gpd.overlay(tracts, boundary, how="intersection")
    tracts_clipped.reset_index(drop=True, inplace=True)
    print(f"  Tracts after clip: {len(tracts_clipped)}")

    # 4) Normalize population field name
    # Your county dataset uses POPULATION as total population
    if "POPULATION" not in tracts_clipped.columns:
        raise KeyError(
            "Expected a 'POPULATION' column in the tract layer but did not find one. "
            "Check the attribute table or print the columns above."
        )

    tracts_clipped = tracts_clipped.rename(columns={"POPULATION": "population"})

    # Ensure GEOID exists and is string
    if "GEOID" not in tracts_clipped.columns:
        raise KeyError(
            "Expected a 'GEOID' column in the tract layer but did not find one."
        )
    tracts_clipped["GEOID"] = tracts_clipped["GEOID"].astype("string")

    # 5) Save as GeoJSON in WGS84 for web mapping
    print("\n[4] Reprojecting to EPSG:4326 and saving…")
    tracts_out = tracts_clipped.to_crs(epsg=4326)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tracts_out.to_file(out_path, driver="GeoJSON")

    print("\n✅ DONE: Saved tracts with population to:")
    print(f"   {out_path}")
    print("\nColumns available:")
    print(list(tracts_out.columns))


if __name__ == "__main__":
    main()
