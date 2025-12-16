from pathlib import Path
import osmnx as ox
import geopandas as gpd

def main():
    place_names = ["City of Los Angeles, California, USA", "Los Angeles, California, USA"]
    
    for place in place_names:
        print(f"\nTesting: {place}")
        try:
            gdf = ox.geocode_to_gdf(place)
            print(f"  Rows: {len(gdf)}")
            geom = gdf.geometry.iloc[0]
            print(f"  Geom Type: {geom.geom_type}")
            print(f"  Bounds: {geom.bounds}")
            
            # Try a quick verify of features
            print("  Attempting to fetch 1 park...")
            # Use a very specific tag or a small limit if possible? 
            # features_from_polygon doesn't have a limit param easily without downloading.
            # We'll just try it inside a try/except
            try:
                parks = ox.features_from_polygon(geom,tags={"leisure": "park"})
                print(f"  Found {len(parks)} parks.")
            except Exception as e:
                print(f"  Error fetching parks: {e}")
                
        except Exception as e:
            print(f"  Geocode failed: {e}")

if __name__ == "__main__":
    main()
