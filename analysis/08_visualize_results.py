from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import folium
from folium import GeoJson
from folium.features import GeoJsonTooltip, GeoJsonPopup


def get_paths():
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    boundary_path = data_dir / "boundary.geojson"
    tracts_access_path = data_dir / "riverside_tracts_accessibility_15min.geojson"
    parks_path = data_dir / "parks.geojson"
    isochrones_path = data_dir / "isochrones" / "parks_isochrones_15min.geojson"
    neighborhoods_access_path = (
        data_dir / "outputs" / "riverside_neighborhoods_accessibility_15min.geojson"
    )

    out_map = project_root / "riverside_tract_accessibility_map.html"

    return (
        boundary_path,
        tracts_access_path,
        parks_path,
        isochrones_path,
        neighborhoods_access_path,
        out_map,
    )


def color_for_score(score: float) -> str:
    """Simple manual color ramp for accessibility_score."""
    if score is None:
        return "#dddddd"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "#dddddd"

    if s < 20:
        return "#ffffcc"  # very low
    elif s < 40:
        return "#c2e699"
    elif s < 60:
        return "#78c679"
    elif s < 80:
        return "#31a354"
    else:
        return "#006837"  # very high


def main() -> None:
    (
        boundary_path,
        tracts_access_path,
        parks_path,
        isochrones_path,
        neighborhoods_access_path,
        out_map,
    ) = get_paths()

    print(f"Boundary file                 : {boundary_path}")
    print(f"Tract accessibility file      : {tracts_access_path}")
    print(f"Neighborhood accessibility    : {neighborhoods_access_path}")
    print(f"Parks file                    : {parks_path}")
    print(f"Isochrones file               : {isochrones_path}")
    print(f"Output map                    : {out_map}")

    # ---------- Load data ---------- #
    boundary = gpd.read_file(boundary_path)
    tracts = gpd.read_file(tracts_access_path)
    parks = gpd.read_file(parks_path)
    isochrones = gpd.read_file(isochrones_path)
    neighborhoods = gpd.read_file(neighborhoods_access_path)

    # Ensure everything is in WGS84 (lat/lon)
    boundary = boundary.to_crs(epsg=4326)
    tracts = tracts.to_crs(epsg=4326)
    parks = parks.to_crs(epsg=4326)
    isochrones = isochrones.to_crs(epsg=4326)
    neighborhoods = neighborhoods.to_crs(epsg=4326)

    # Center the map on the city centroid
    city_centroid = boundary.geometry.unary_union.centroid
    center_lat = city_centroid.y
    center_lon = city_centroid.x

    # ---------- Base map ---------- #
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles=None)

    folium.TileLayer(
        "cartodbpositron",
        name="Basemap",
        control=True,
    ).add_to(m)

    # ---------- Tract accessibility layer ---------- #
    print("Adding tract accessibility layer (styled + clickable)…")

    tract_tooltip = GeoJsonTooltip(
        fields=["GEOID", "population", "accessibility_score"],
        aliases=["GEOID", "Population", "Accessibility score"],
        localize=True,
    )

    tract_popup = GeoJsonPopup(
        fields=["GEOID", "population", "accessibility_score"],
        aliases=[
            "GEOID:",
            "Population:",
            "Accessibility score (0–100):",
        ],
        localize=True,
    )

    def tract_style(feature):
        score = feature["properties"].get("accessibility_score")
        return {
            "fillColor": color_for_score(score),
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    GeoJson(
        tracts,
        name="Accessibility by tract",
        style_function=tract_style,
        highlight_function=lambda feature: {
            "weight": 2,
            "color": "blue",
        },
        tooltip=tract_tooltip,
        popup=tract_popup,
        show=True,  # visible by default
    ).add_to(m)

    # ---------- Neighborhood accessibility layer ---------- #
    print("Adding neighborhood accessibility layer…")

    # Neighborhood fields expected from 11_compute_accessibility_neighborhoods.py:
    # - neighborhood_name
    # - total_population
    # - total_pop_within_15
    # - neigh_coverage_fraction
    # - neigh_accessibility_score

    neigh_tooltip = GeoJsonTooltip(
        fields=[
            "neighborhood_name",
            "total_population",
            "total_pop_within_15",
            "neigh_coverage_fraction",
            "neigh_accessibility_score",
        ],
        aliases=[
            "Neighborhood",
            "Total population",
            "Pop within 15 min",
            "Coverage fraction",
            "Accessibility score",
        ],
        localize=True,
    )

    neigh_popup = GeoJsonPopup(
        fields=[
            "neighborhood_name",
            "total_population",
            "total_pop_within_15",
            "neigh_coverage_fraction",
            "neigh_accessibility_score",
        ],
        aliases=[
            "Neighborhood:",
            "Total population:",
            "Population within 15-min walk:",
            "Coverage fraction:",
            "Accessibility score (0–100):",
        ],
        localize=True,
    )

    def neigh_style(feature):
        score = feature["properties"].get("neigh_accessibility_score")
        return {
            "fillColor": color_for_score(score),
            "color": "black",
            "weight": 1.0,
            "fillOpacity": 0.6,
        }

    GeoJson(
        neighborhoods,
        name="Accessibility by neighborhood",
        style_function=neigh_style,
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "darkred",
        },
        tooltip=neigh_tooltip,
        popup=neigh_popup,
        show=False,  # start hidden; user can toggle on
    ).add_to(m)

    # ---------- Isochrones outline layer ---------- #
    print("Adding isochrones layer…")

    GeoJson(
        isochrones,
        name="15-minute park isochrones",
        style_function=lambda feature: {
            "color": "#1f77b4",
            "weight": 1,
            "fillOpacity": 0.1,
        },
        show=True,
    ).add_to(m)

    # ---------- Parks layer ---------- #
    print("Adding parks layer…")

    GeoJson(
        parks,
        name="Parks",
        marker=folium.CircleMarker(
            radius=3,
            color="darkgreen",
            fill=True,
            fill_opacity=1,
        ),
        tooltip=GeoJsonTooltip(
            fields=["name"] if "name" in parks.columns else [],
            aliases=["Park name"],
            localize=True,
        ),
        show=True,
    ).add_to(m)

    # ---------- Boundary outline ---------- #
    GeoJson(
        boundary,
        name="City boundary",
        style_function=lambda feature: {
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.0,
        },
        show=True,
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(out_map))
    print("\n✅ DONE: Saved accessibility map to:")
    print(f"   {out_map}")


if __name__ == "__main__":
    main()
