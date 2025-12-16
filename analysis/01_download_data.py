from pathlib import Path
import osmnx as ox
import geopandas as gpd
import sys

# Configure OSMnx
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.requests_timeout = 1200

def main() -> None:
    try:
        # Resolve the ../data directory relative to this file
        project_root = Path(__file__).resolve().parents[1]
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        print(f"Using data directory: {data_dir}", flush=True)

        # ------------------------------------------------------------------ #
        # 1. Choose the study area
        # ------------------------------------------------------------------ #
        place_name = "Riverside, California, USA"
        print(f"\n[1] Downloading boundary for: {place_name}", flush=True)

        boundary_gdf = ox.geocode_to_gdf(place_name)
        boundary_path = data_dir / "boundary.geojson"
        boundary_gdf.to_file(boundary_path, driver="GeoJSON")
        print(f"    ✔ Saved boundary to: {boundary_path}", flush=True)

        # ------------------------------------------------------------------ #
        # 2. Download walking street network for the area
        # ------------------------------------------------------------------ #
        # NOTE: LA is huge. This might fail or take a long time.
        print("\n[2] Downloading walking street network (this may take a while)...", flush=True)
        try:
            # simple version first
            graph = ox.graph_from_place(place_name, network_type="walk")
            print(f"    Graph stats → nodes: {len(graph.nodes)}, edges: {len(graph.edges)}", flush=True)

            street_graph_path = data_dir / "street_network.graphml"
            ox.save_graphml(graph, street_graph_path)
            print(f"    ✔ Saved street graph to: {street_graph_path}", flush=True)
        except Exception as e:
            print(f"    ❌ Failed to download/save graph: {e}", flush=True)
            # Proceeding without graph might break next steps, but let's see features first
            
        # ------------------------------------------------------------------ #
        # 3. Download park features inside the boundary
        # ------------------------------------------------------------------ #
        print("\n[3] Downloading parks within boundary…", flush=True)
        boundary_geom = boundary_gdf.geometry.iloc[0]
        park_tags = {"leisure": "park"}

        parks_gdf = ox.features_from_polygon(boundary_geom, park_tags)
        print(f"    Found {len(parks_gdf)} features", flush=True)

        # Keep only essential columns: name + geometry
        keep_cols = [c for c in parks_gdf.columns if c in ("name", "geometry")]
        parks_gdf = parks_gdf[keep_cols].copy()
        parks_gdf["name"] = parks_gdf["name"].fillna("Unnamed park")

        parks_path = data_dir / "parks.geojson"
        parks_gdf.to_file(parks_path, driver="GeoJSON")
        print(f"    ✔ Saved parks to: {parks_path}", flush=True)

        # ------------------------------------------------------------------ #
        # Summary
        # ------------------------------------------------------------------ #
        print("\n✅ DONE: Base data downloaded.", flush=True)

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
