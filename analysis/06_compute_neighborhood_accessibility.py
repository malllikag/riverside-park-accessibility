"""
06_compute_neighborhood_accessibility.py

Aggregate tract-level accessibility metrics to neighborhood polygons.

Inputs:
- data/intermediate/riverside_neighborhoods_clean.geojson
    (created by 05_prepare_neighborhoods.py, contains:
        - neighborhood_name
        - geometry
    )

- data/outputs/riverside_tract_accessibility_15min.geojson
    (created by 04_compute_tract_accessibility.py, expected to contain:
        - geometry
        - population (total population per tract)
        - pop_within_15 (people within 15-min walk of a park)
        - coverage_fraction (optional; can be recomputed)
        - accessibility_score (tract-level score)

Output:
- data/outputs/riverside_neighborhoods_accessibility_15min.geojson
    One row per neighborhood, with:
        - neighborhood_name
        - total_population
        - total_pop_within_15
        - neigh_coverage_fraction
        - neigh_accessibility_score
        - geometry
"""

from pathlib import Path
import logging

import geopandas as gpd
import pandas as pd
import numpy as np


# -----------------------------------------------
# Configuration
# -----------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

NEIGHBORHOODS_PATH = DATA_DIR / "intermediate" / "riverside_neighborhoods_clean.geojson"
TRACTS_ACCESS_PATH = DATA_DIR / "riverside_tracts_accessibility_15min.geojson"
OUTPUT_PATH = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min.geojson"

# Column names
NEIGH_NAME = "neighborhood_name"
TRACT_POP = "population"
TRACT_POP15 = "pop_within_15"
TRACT_SCORE = "accessibility_score"


# -----------------------------------------------
# Logging
# -----------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------
# Helper functions
# -----------------------------------------------

def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Compute a weighted mean, handling edge cases where weights sum to zero."""
    w_sum = weights.sum()
    if w_sum <= 0:
        return np.nan
    return float((values * weights).sum() / w_sum)


# -----------------------------------------------
# Main
# -----------------------------------------------

def main() -> None:
    logger.info("Loading cleaned neighborhoods...")
    gdf_neigh = gpd.read_file(NEIGHBORHOODS_PATH)

    logger.info("Loading tract accessibility...")
    gdf_tracts = gpd.read_file(TRACTS_ACCESS_PATH)

    # Sanity check: required tract columns
    missing = [c for c in [TRACT_POP, TRACT_POP15, TRACT_SCORE, "geometry"] if c not in gdf_tracts.columns]
    if missing:
        raise KeyError(
            f"Tract accessibility file is missing required columns: {missing}. "
            f"Available: {list(gdf_tracts.columns)}"
        )

    # CRS alignment (use tract CRS as canonical)
    if gdf_neigh.crs != gdf_tracts.crs:
        logger.info(f"Reprojecting neighborhoods from {gdf_neigh.crs} to {gdf_tracts.crs}")
        gdf_neigh = gdf_neigh.to_crs(gdf_tracts.crs)

    # Spatial join: assign each tract to a neighborhood
    logger.info("Performing spatial join (tracts → neighborhoods, predicate='intersects')...")
    tracts_joined = gpd.sjoin(
        gdf_tracts,
        gdf_neigh[[NEIGH_NAME, "geometry"]],
        how="inner",
        predicate="intersects",
    )

    if tracts_joined.empty:
        raise ValueError("Spatial join returned no matches. Check CRS and geometry overlap.")

    logger.info(f"Spatial join produced {len(tracts_joined)} tract–neighborhood rows")

    # Aggregate metrics per neighborhood
    logger.info("Aggregating metrics per neighborhood...")

    grouped = tracts_joined.groupby(NEIGH_NAME).agg(
        total_population=(TRACT_POP, "sum"),
        total_pop_within_15=(TRACT_POP15, "sum"),
    )

    grouped["neigh_coverage_fraction"] = (
        grouped["total_pop_within_15"] / grouped["total_population"]
    )

    grouped["neigh_accessibility_score"] = (
        tracts_joined.groupby(NEIGH_NAME).apply(
            lambda df: weighted_mean(df[TRACT_SCORE], df[TRACT_POP])
        )
    )

    grouped.reset_index(inplace=True)

    # Merge back onto neighborhood geometries
    logger.info("Merging aggregated metrics back onto neighborhoods...")
    gdf_out = gdf_neigh.merge(grouped, on=NEIGH_NAME, how="left")

    # Warn if any neighborhoods have no attached metrics
    missing_metrics = gdf_out[gdf_out["total_population"].isna()]
    if not missing_metrics.empty:
        logger.warning(
            f"{len(missing_metrics)} neighborhoods have no intersecting tracts / metrics."
        )

    # Save output
    logger.info(f"Saving neighborhood accessibility → {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdf_out.to_file(OUTPUT_PATH, driver="GeoJSON")

    logger.info("Neighborhood accessibility computed successfully!")


if __name__ == "__main__":
    main()
