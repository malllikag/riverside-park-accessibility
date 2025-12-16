from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def get_paths():
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    tracts_with_pop = data_dir / "riverside_tracts_with_population.geojson"
    isochrones_path = data_dir / "isochrones" / "parks_isochrones_15min.geojson"
    out_path = data_dir / "riverside_tracts_accessibility_15min.geojson"

    return tracts_with_pop, isochrones_path, out_path


def main() -> None:
    tracts_path, isos_path, out_path = get_paths()

    print(f"Tracts with pop : {tracts_path}")
    print(f"Isochrones file : {isos_path}")

    if not tracts_path.exists():
        raise FileNotFoundError(f"Missing tracts file: {tracts_path}")
    if not isos_path.exists():
        raise FileNotFoundError(f"Missing isochrones file: {isos_path}")

    print("\n[1] Loading data…")
    tracts = gpd.read_file(tracts_path)
    isos = gpd.read_file(isos_path)

    print(f"  Tracts: {len(tracts)}")
    print(f"  Isochrones: {len(isos)}")

    # Work in projected CRS for area calculations
    utm_crs = tracts.estimate_utm_crs()
    tracts_utm = tracts.to_crs(utm_crs)
    isos_utm = isos.to_crs(utm_crs)

    print("\n[2] Building union of all park isochrones…")
    iso_union = isos_utm.unary_union

    print("[3] Computing coverage + accessibility per tract…")

    coverage_fraction = []
    pop_within_15 = []

    for idx, row in tracts_utm.iterrows():
        geom = row.geometry
        total_pop = float(row.get("population", 0) or 0)

        if geom is None or geom.is_empty or total_pop <= 0:
            coverage_fraction.append(0.0)
            pop_within_15.append(0.0)
            continue

        tract_area = geom.area
        if tract_area <= 0:
            coverage_fraction.append(0.0)
            pop_within_15.append(0.0)
            continue

        inter = geom.intersection(iso_union)
        if inter.is_empty:
            frac = 0.0
        else:
            frac = float(inter.area / tract_area)

        # Clamp to [0, 1]
        frac = max(0.0, min(1.0, frac))

        coverage_fraction.append(frac)
        pop_within_15.append(total_pop * frac)

    tracts_utm["coverage_fraction"] = coverage_fraction
    tracts_utm["pop_within_15"] = pop_within_15
    tracts_utm["total_pop"] = tracts_utm["population"]

    # Avoid division by zero
    denom = tracts_utm["total_pop"].where(tracts_utm["total_pop"] > 0, 1.0)

    tracts_utm["accessibility_score"] = 100.0 * tracts_utm["pop_within_15"] / denom

    # Back to WGS84 for web maps
    tracts_out = tracts_utm.to_crs("EPSG:4326")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tracts_out.to_file(out_path, driver="GeoJSON")

    print("\n✅ DONE: Saved tract-level accessibility to:")
    print(f"   {out_path}")


if __name__ == "__main__":
    main()
