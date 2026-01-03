from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# === INPUT / OUTPUT ===
INPUT_PATH = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min.geojson"
OUTPUT_PATH = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min_flagged.geojson"

# Optional: also flag neighborhoods where MOST residents lack access
UNDERSERVED_PCT_THRESHOLD = 50.0  # set to None to disable


def first_key(props: dict, candidates: list[str]) -> str | None:
    for k in candidates:
        if k in props:
            return k
    return None


def to_int(x, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(round(float(x)))
    except Exception:
        return default


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input GeoJSON not found: {INPUT_PATH}")

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        gjson = json.load(f)

    if "features" not in gjson or not isinstance(gjson["features"], list) or len(gjson["features"]) == 0:
        raise ValueError("Input file is not a valid GeoJSON FeatureCollection with features.")

    # Detect field names from the first feature (so this works even if your schema differs slightly)
    sample_props = gjson["features"][0].get("properties", {})

    total_pop_key = first_key(
        sample_props,
        ["total_pop", "total_population", "POPULATION", "population", "neigh_total_pop"],
    )
    pop_within_15_key = first_key(
        sample_props,
        ["pop_within_15", "total_pop_within_15", "neigh_pop_within_15", "pop15"],
    )
    name_key = first_key(
        sample_props,
        ["neighborhood_name", "NAME", "name", "NAMELSAD"],
    )

    if total_pop_key is None or pop_within_15_key is None:
        raise ValueError(
            "Could not find required fields in neighborhood GeoJSON.\n"
            "Expected total population and population within 15 minutes.\n\n"
            f"Detected properties keys: {sorted(list(sample_props.keys()))}\n\n"
            "Rename your output fields to 'total_pop' and 'pop_within_15' OR update the key lists in this script."
        )

    strict_count = 0
    threshold_count = 0

    for feat in gjson["features"]:
        props = feat.get("properties", {})

        total_pop = to_int(props.get(total_pop_key), default=0)
        pop_within_15 = to_int(props.get(pop_within_15_key), default=0)

        # Guardrails
        if total_pop < 0:
            total_pop = 0
        if pop_within_15 < 0:
            pop_within_15 = 0
        if pop_within_15 > total_pop:
            pop_within_15 = total_pop

        pop_without_15 = total_pop - pop_within_15
        pct_without_15 = 0.0 if total_pop == 0 else (100.0 * pop_without_15 / total_pop)

        # STRICT definition (your wording): no residents have 15-min access
        is_underserved = (total_pop > 0) and (pop_within_15 == 0)

        # Optional threshold definition: most residents lack access
        is_underserved_threshold = False
        if UNDERSERVED_PCT_THRESHOLD is not None and total_pop > 0:
            is_underserved_threshold = (pct_without_15 >= float(UNDERSERVED_PCT_THRESHOLD))

        # Write fields back into GeoJSON
        props["pop_without_15"] = pop_without_15
        props["pct_without_15"] = round(pct_without_15, 2)
        props["is_underserved"] = bool(is_underserved)
        props["is_underserved_threshold"] = bool(is_underserved_threshold)
        props["underserved_threshold_pct"] = None if UNDERSERVED_PCT_THRESHOLD is None else float(UNDERSERVED_PCT_THRESHOLD)

        # Nice-to-have label for popups
        if "label" not in props:
            props["label"] = props.get(name_key) if name_key else None

        strict_count += int(is_underserved)
        threshold_count += int(is_underserved_threshold)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(gjson, f)

    print("Flagging complete.")
    print(f"Input:  {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Detected fields: total_pop='{total_pop_key}', pop_within_15='{pop_within_15_key}', name='{name_key}'")
    print(f"Strict underserved (pop_within_15 == 0): {strict_count}")
    if UNDERSERVED_PCT_THRESHOLD is not None:
        print(f"Threshold underserved (pct_without_15 >= {UNDERSERVED_PCT_THRESHOLD}%): {threshold_count}")


if __name__ == "__main__":
    main()
