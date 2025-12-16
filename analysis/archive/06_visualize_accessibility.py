from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd


def get_paths():
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    boundary_path = data_dir / "boundary.geojson"
    parks_path = data_dir / "parks.geojson"
    isochrones_path = data_dir / "isochrones" / "parks_isochrones_15min.geojson"
    accessibility_path = data_dir / "accessibility_cells_15min.geojson"
    output_map = project_root / "la_parks_accessibility_map.html"
    return (
        data_dir,
        boundary_path,
        parks_path,
        isochrones_path,
        accessibility_path,
        output_map,
    )


def main() -> None:
    (
        data_dir,
        boundary_path,
        parks_path,
        isochrones_path,
        accessibility_path,
        output_map,
    ) = get_paths()

    print(f"Data dir: {data_dir}")

    # Load layers
    boundary = gpd.read_file(boundary_path)
    parks = gpd.read_file(parks_path)
    isochrones = gpd.read_file(isochrones_path)
    cells = gpd.read_file(accessibility_path)

    # Center map on boundary centroid
    boundary_centroid = boundary.geometry.iloc[0].centroid
    center_lat = boundary_centroid.y
    center_lon = boundary_centroid.x

    print(f"Map center → lat: {center_lat:.6f}, lon: {center_lon:.6f}")

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="cartodbpositron")

    # --- Accessibility cells (choropleth style) ---
    # Normalize scores for color ramp: 0 → red, 100 → green
    def cell_style(feature):
        score = feature["properties"].get("accessibility_score", 0)
        # clamp
        score = max(0, min(100, score))
        # simple red→green mix
        # 0 = red (255,0,0), 100 = green (0,255,0)
        r = int(255 * (100 - score) / 100)
        g = int(255 * score / 100)
        b = 0
        return {
            "fillColor": f"rgb({r},{g},{b})",
            "color": None,
            "weight": 0,
            "fillOpacity": 0.6,
        }

    folium.GeoJson(
        cells,
        name="Accessibility cells (0–100)",
        style_function=cell_style,
        tooltip=folium.GeoJsonTooltip(
            fields=["population", "pop_within_15", "accessibility_score"],
            aliases=["Population", "Pop within 15 min", "Score"],
            localize=True,
        ),
    ).add_to(m)

    # --- Isochrones (park 15-min bubbles) ---
    folium.GeoJson(
        isochrones,
        name="Park 15-min isochrones",
        style_function=lambda feat: {
            "fillColor": "blue",
            "color": "blue",
            "weight": 1,
            "fillOpacity": 0.1,
        },
        tooltip=folium.GeoJsonTooltip(fields=["park_name"], aliases=["Park"]),
    ).add_to(m)

    # --- Parks as points/centroids ---
    parks_points = parks.copy()
    parks_points["geometry"] = parks_points.geometry.centroid

    for _, row in parks_points.iterrows():
        name = row.get("name", "Park")
        geom = row.geometry
        folium.CircleMarker(
            location=[geom.y, geom.x],
            radius=3,
            popup=name,
            tooltip=name,
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(output_map))
    print(f"\n✅ Map saved to:\n   {output_map}")
    print("Open this file in your browser to explore the results.")


if __name__ == "__main__":
    main()
