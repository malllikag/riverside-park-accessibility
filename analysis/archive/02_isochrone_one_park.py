from __future__ import annotations

from pathlib import Path
from typing import Tuple, List

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Polygon


# ----------------------------- Configuration ----------------------------- #

# Walking speed (km/h)
WALK_SPEED_KMH: float = 5.0

# Isochrone time in minutes
ISOCHRONE_MINUTES: int = 15


# ----------------------------- Helper Functions -------------------------- #

def get_project_paths() -> Tuple[Path, Path, Path, Path]:
    """
    Resolve the project root and commonly used paths.

    Returns:
        (project_root, data_dir, graph_path, parks_path)
    """
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    graph_path = data_dir / "street_network.graphml"
    parks_path = data_dir / "parks.geojson"
    return project_root, data_dir, graph_path, parks_path


def load_graph(graph_path: Path) -> nx.MultiDiGraph:
    """Load the walking street network graph from disk."""
    print(f"Loading street network from: {graph_path}")
    graph = ox.load_graphml(graph_path)
    print(f"  Loaded graph → nodes: {len(graph.nodes)}, edges: {len(graph.edges)}")
    return graph


def load_parks(parks_path: Path) -> gpd.GeoDataFrame:
    """Load the parks layer from disk."""
    print(f"Loading parks from: {parks_path}")
    parks_gdf = gpd.read_file(parks_path)
    print(f"  Loaded {len(parks_gdf)} park features")
    return parks_gdf


def add_travel_time_to_edges(graph: nx.MultiDiGraph, walk_speed_kmh: float) -> None:
    """
    Add a 'travel_time' attribute (seconds) to each edge in the graph
    based on its length and the assumed walking speed.
    """
    walk_speed_m_per_s = (walk_speed_kmh * 1000) / 3600.0

    for u, v, k, data in graph.edges(keys=True, data=True):
        length_m = data.get("length", 0.0)
        travel_time_s = length_m / walk_speed_m_per_s if length_m > 0 else 0.0
        data["travel_time"] = travel_time_s

    print("  Added 'travel_time' (seconds) to all edges")


def compute_reachable_nodes(
    graph: nx.MultiDiGraph,
    source_node: int,
    max_travel_time_min: int,
) -> List[int]:
    """
    Compute all graph nodes reachable from source_node within
    max_travel_time_min using the 'travel_time' edge attribute.

    Returns:
        List of reachable node IDs.
    """
    max_travel_time_s = max_travel_time_min * 60

    # Use Dijkstra to compute shortest travel_time from source to all nodes
    travel_times = nx.single_source_dijkstra_path_length(
        graph,
        source=source_node,
        weight="travel_time",
        cutoff=max_travel_time_s,
    )

    reachable_nodes = list(travel_times.keys())
    print(f"  Reachable nodes within {max_travel_time_min} min: {len(reachable_nodes)}")
    return reachable_nodes


def build_isochrone_polygon(
    graph: nx.MultiDiGraph,
    reachable_nodes: List[int],
) -> Polygon:
    """
    Convert the set of reachable nodes into a single polygon.
    For now we use a convex hull of the node geometries as a simple approximation.
    """
    # Convert graph to GeoDataFrames
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    sub_nodes = nodes_gdf.loc[reachable_nodes]

    # Combine all node points into a single geometry, then take convex hull
    combined_geom = sub_nodes.unary_union
    polygon = combined_geom.convex_hull

    return polygon


# ----------------------------- Main Workflow ----------------------------- #

def main() -> None:
    project_root, data_dir, graph_path, parks_path = get_project_paths()
    print(f"Project root: {project_root}")
    print(f"Data directory: {data_dir}")

    # Ensure isochrones directory exists
    isochrone_dir = data_dir / "isochrones"
    isochrone_dir.mkdir(exist_ok=True)

    # 1. Load graph and parks
    graph = load_graph(graph_path)
    parks_gdf = load_parks(parks_path)

    # 2. Pick a single park (for now, the first one)
    if parks_gdf.empty:
        raise RuntimeError("No parks found in parks.geojson")

    park = parks_gdf.iloc[0]
    park_name = park.get("name", "Unnamed park")
    park_geom = park.geometry

    print(f"\nUsing park: {park_name}")

    # 3. Find nearest graph node to the park centroid
    centroid = park_geom.centroid
    park_lon = centroid.x
    park_lat = centroid.y

    print(f"  Park centroid → lat: {park_lat:.6f}, lon: {park_lon:.6f}")

    source_node = ox.distance.nearest_nodes(graph, X=park_lon, Y=park_lat)
    print(f"  Nearest graph node ID: {source_node}")

    # 4. Add travel_time to edges and compute reachable nodes
    print("\nComputing reachable nodes based on walking travel time...")
    add_travel_time_to_edges(graph, WALK_SPEED_KMH)
    reachable_nodes = compute_reachable_nodes(
        graph,
        source_node=source_node,
        max_travel_time_min=ISOCHRONE_MINUTES,
    )

    if not reachable_nodes:
        raise RuntimeError("No reachable nodes found within time threshold")

    # 5. Build isochrone polygon
    print("\nBuilding isochrone polygon...")
    isochrone_polygon = build_isochrone_polygon(graph, reachable_nodes)

    # 6. Save isochrone as a GeoJSON file
    isochrone_gdf = gpd.GeoDataFrame(
        [
            {
                "park_name": park_name,
                "minutes": ISOCHRONE_MINUTES,
                "geometry": isochrone_polygon,
            }
        ],
        crs="EPSG:4326",  # graph is in lat/lon (WGS84) by default
    )

    isochrone_path = isochrone_dir / "park_0_isochrone_15min.geojson"
    isochrone_gdf.to_file(isochrone_path, driver="GeoJSON")
    print(f"  ✔ Saved isochrone to: {isochrone_path}")

    print("\n✅ DONE: First 15-minute walking isochrone generated.")


if __name__ == "__main__":
    main()
