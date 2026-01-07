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


def compute_reachable_nodes_multi_source(
    G: nx.MultiDiGraph, source_nodes: List[int], max_minutes: int
) -> List[int]:
    """Computation using multiple source nodes (entrances)."""
    max_seconds = max_minutes * 60
    # nx doesn't have a direct multi-source Dijkstra with cutoff in one call easily for all lengths, 
    # but we can simulate it by running from multiple sources.
    all_reachable = set()
    for node in source_nodes:
        times = nx.single_source_dijkstra_path_length(
            G,
            source=node,
            weight="travel_time",
            cutoff=max_seconds,
        )
        all_reachable.update(times.keys())
    return list(all_reachable)


def build_isochrone_polygon_tighter(
    G: nx.MultiDiGraph,
    reachable_nodes: List[int],
) -> Polygon:
    """Builds a tighter polygon by buffering reachable nodes instead of a convex hull."""
    nodes_gdf = ox.graph_to_gdfs(G, nodes=True, edges=False)
    sub_nodes = nodes_gdf.loc[reachable_nodes]
    
    # Buffer nodes by 50m to create a continuous reachability surface
    # This acts like a 'concave hull' that follows the streets.
    # Convert to UTM for accurate buffering in meters
    utm_crs = nodes_gdf.estimate_utm_crs()
    sub_nodes_utm = sub_nodes.to_crs(utm_crs)
    
    buffered = sub_nodes_utm.buffer(60) # 60 meters buffer to close gaps between nodes
    combined = buffered.unary_union
    
    # Simplify and convert back to 4326
    tight_poly = combined.simplify(10)
    return gpd.GeoSeries([tight_poly], crs=utm_crs).to_crs("EPSG:4326").iloc[0]


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

    print("\nGenerating HIGH-ACCURACY isochrones for parks…")
    for idx, park in parks.iterrows():
        park_name = park.get("name", "Unnamed park")
        geom = park.geometry

        if geom is None or geom.is_empty:
            continue

        # MULTI-ENTRANCE LOGIC:
        # Instead of centroid, sample points along the boundary every 30 meters
        # This handles large parks where you can enter from any side.
        try:
            boundary = geom.boundary
            if boundary.is_empty: # Point parks
                sample_points = [geom]
            else:
                # Calculate number of samples based on perimeter length
                # Approx every 50m
                num_samples = max(4, int(boundary.length / 0.0005)) # ~50m in degrees roughly
                sample_points = [boundary.interpolate(i/num_samples, normalized=True) for i in range(num_samples)]
            
            source_nodes = []
            for pt in sample_points:
                node = ox.distance.nearest_nodes(G, X=pt.x, Y=pt.y)
                source_nodes.append(node)
                
            # Remove duplicates
            source_nodes = list(set(source_nodes))
            
        except Exception as ex:
            print(f"  [skip] Park {idx} ({park_name}): entrance sampling failed → {ex}")
            continue

        reachable = compute_reachable_nodes_multi_source(G, source_nodes, ISOCHRONE_MINUTES)
        if not reachable:
            print(f"  [skip] Park {idx} ({park_name}): no reachable nodes")
            continue

        try:
            # Use the tighter polygon builder
            polygon = build_isochrone_polygon_tighter(G, reachable)
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

        print(f"  ✔ {park_name}: {len(source_nodes)} entrances, {len(reachable)} nodes reachable")

    if not features:
        raise RuntimeError("No isochrones could be built.")

    isochrones_gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")

    out_path = isochrone_dir / f"parks_isochrones_{ISOCHRONE_MINUTES}min.geojson"
    isochrones_gdf.to_file(out_path, driver="GeoJSON")

    print(f"\n✅ DONE: Saved {len(isochrones_gdf)} ACCURATE isochrones to:")
    print(f"   {out_path}")


if __name__ == "__main__":
    main()
