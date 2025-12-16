from __future__ import annotations

from pathlib import Path
from typing import Tuple, List

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Polygon

# ----------------------------- Configuration ----------------------------- #

WALK_SPEED_KMH: float = 5.0          # walking speed
ISOCHRONE_MINUTES: int = 15          # time threshold in minutes
MAX_PARKS: int | None = None         # set to e.g. 20 while testing, None = all


# ----------------------------- Helpers ---------------------------------- #

def get_paths() -> Tuple[Path, Path, Path, Path]:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    graph_path = data_dir / "street_network.graphml"
    parks_path = data_dir / "parks.geojson"
    return project_root, data_dir, graph_path, parks_path


def load_graph(graph_path: Path) -> nx.MultiDiGraph:
    print(f"Loading graph from: {graph_path}")
    G = ox.load_graphml(graph_path)
    print(f"  nodes: {len(G.nodes)}, edges: {len(G.edges)}")
    return G


def load_parks(parks_path: Path) -> gpd.GeoDataFrame:
    print(f"Loading parks from: {parks_path}")
    parks = gpd.read_file(parks_path)
    print(f"  parks: {len(parks)}")
    return parks


def add_travel_time_to_edges(G: nx.MultiDiGraph, walk_speed_kmh: float) -> None:
    walk_speed_mps = walk_speed_kmh * 1000 / 3600.0
    for u, v, k, data in G.edges(keys=True, data=True):
        length_m = data.get("length", 0.0)
        data["travel_time"] = length_m / walk_speed_mps if length_m > 0 else 0.0
    print("  added 'travel_time' to edges")


def compute_reachable_nodes(
    G: nx.MultiDiGraph, source_node: int, max_minutes: int
) -> List[int]:
    max_seconds = max_minutes * 60
    times = nx.single_source_dijkstra_path_length(
        G,
        source=source_node,
        weight="travel_time",
        cutoff=max_seconds,
    )
    return list(times.keys())


def build_isochrone_polygon(
    G: nx.MultiDiGraph,
    reachable_nodes: List[int],
) -> Polygon:
    nodes_gdf = ox.graph_to_gdfs(G, nodes=True, edges=False)
    sub_nodes = nodes_gdf.loc[reachable_nodes]
    combined = sub_nodes.unary_union
    return combined.convex_hull


# ----------------------------- Main ------------------------------------- #

def main() -> None:
    project_root, data_dir, graph_path, parks_path = get_paths()
    print(f"Project root: {project_root}")
    print(f"Data dir: {data_dir}")

    isochrone_dir = data_dir / "isochrones"
    isochrone_dir.mkdir(exist_ok=True)

    G = load_graph(graph_path)
    parks = load_parks(parks_path)

    if parks.empty:
        raise RuntimeError("No parks available.")

    print("\nPreparing graph with travel_time…")
    add_travel_time_to_edges(G, WALK_SPEED_KMH)

    # Optional: limit number of parks while testing
    if MAX_PARKS is not None:
        parks = parks.iloc[:MAX_PARKS].copy()
        print(f"\n⚠ Limiting to first {len(parks)} parks for testing")

    features: list[dict] = []

    print("\nGenerating isochrones for parks…")
    for idx, park in parks.iterrows():
        park_name = park.get("name", "Unnamed park")
        geom = park.geometry

        if geom is None or geom.is_empty:
            print(f"  [skip] Park {idx} has no valid geometry")
            continue

        centroid = geom.centroid
        lon, lat = centroid.x, centroid.y

        try:
            source_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
        except Exception as ex:
            print(f"  [skip] Park {idx} ({park_name}): nearest node failed → {ex}")
            continue

        reachable = compute_reachable_nodes(G, source_node, ISOCHRONE_MINUTES)
        if not reachable:
            print(f"  [skip] Park {idx} ({park_name}): no reachable nodes")
            continue

        try:
            polygon = build_isochrone_polygon(G, reachable)
        except Exception as ex:
            print(f"  [skip] Park {idx} ({park_name}): polygon build failed → {ex}")
            continue

        features.append(
            {
                "park_id": int(idx),
                "park_name": park_name,
                "minutes": ISOCHRONE_MINUTES,
                "geometry": polygon,
            }
        )

        print(f"  ✔ Park {idx} ({park_name}): isochrone built with {len(reachable)} nodes")

    if not features:
        raise RuntimeError("No isochrones could be built for any park.")

    isochrones_gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")

    out_path = isochrone_dir / f"parks_isochrones_{ISOCHRONE_MINUTES}min.geojson"
    isochrones_gdf.to_file(out_path, driver="GeoJSON")

    print(f"\n✅ DONE: Saved {len(isochrones_gdf)} isochrones to:")
    print(f"   {out_path}")


if __name__ == "__main__":
    main()
