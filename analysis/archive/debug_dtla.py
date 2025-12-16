from pathlib import Path
import osmnx as ox
import geopandas as gpd

def main():
    place_name = "Santa Monica, California, USA"
    print(f"Testing: {place_name}")
    try:
        gdf = ox.geocode_to_gdf(place_name)
        print(f"  Rows: {len(gdf)}")
        geom = gdf.geometry.iloc[0]
        
        print("  Downloading graph...")
        G = ox.graph_from_polygon(geom, network_type="walk")
        print(f"  Graph nodes: {len(G.nodes)}")
        
    except Exception as e:
        print(f"  Failed: {e}")

if __name__ == "__main__":
    main()
