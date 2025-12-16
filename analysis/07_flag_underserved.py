import json
from pathlib import Path

# Paths
DATA_DIR = Path("data")
NEIGHBORHOODS_ACCESS_PATH = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min.geojson"

def main():
    with NEIGHBORHOODS_ACCESS_PATH.open("r", encoding="utf-8") as f:
        gjson = json.load(f)

    for feature in gjson["features"]:
        props = feature["properties"]

        total_pop = props.get("total_population", 0) or 0
        pop_15 = props.get("total_pop_within_15", 0) or 0
        frac = props.get("neigh_coverage_fraction", 0) or 0.0

        # Strict rule: no one within 15-minute walk
        is_underserved_strict = (pop_15 <= 0) or (frac <= 0.001)

        props["is_underserved"] = bool(is_underserved_strict)

    with NEIGHBORHOADS_ACCESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(gjson, f)

    print("Updated neighborhoods file with is_underserved flag.")

if __name__ == "__main__":
    main()
