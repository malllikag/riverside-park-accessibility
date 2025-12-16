"""
05_prepare_neighborhoods.py

Prepare Riverside neighborhood polygons for the park accessibility pipeline.

Steps:
1. Load raw neighborhood shapefile and city boundary.
2. Align CRS between layers.
3. Clip neighborhoods to the city boundary.
4. Standardize a canonical neighborhood_name field.
5. Save cleaned neighborhoods as GeoJSON for downstream scripts.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Project root is assumed to be one level above this script (i.e., `analysis/`).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Path to the raw neighborhoods dataset (shapefile or other vector format).
# TODO: Update this if your filename is different.
RAW_NEIGHBORHOODS_PATH = DATA_DIR / "neighborhood_data" / "Riverside_Neighborhoods.shp"

# Path to the city boundary produced by 01_download_data.py
BOUNDARY_PATH = DATA_DIR / "boundary.geojson"

# Output path for the cleaned neighborhoods file
OUTPUT_NEIGHBORHOODS_PATH = (
    DATA_DIR / "intermediate" / "riverside_neighborhoods_clean.geojson"
)

# Column in the raw neighborhoods file that contains the neighborhood name
# TODO: Change this to the actual column name in your shapefile
RAW_NAME_COLUMN = "Neighborho"

# Canonical column name used throughout the project
STANDARDIZED_NAME_COLUMN = "neighborhood_name"


# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def ensure_directory(path: Path) -> None:
    """
    Ensure that the parent directory for a given path exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def load_boundary(path: Path) -> gpd.GeoDataFrame:
    """
    Load the city boundary as a GeoDataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Boundary file not found: {path}")

    logger.info(f"Loading city boundary from {path}")
    boundary_gdf = gpd.read_file(path)

    if boundary_gdf.empty:
        raise ValueError(f"Boundary file is empty: {path}")

    if boundary_gdf.crs is None:
        logger.warning(
            "Boundary file has no CRS set. Consider fixing this upstream."
        )

    return boundary_gdf


def load_neighborhoods(path: Path) -> gpd.GeoDataFrame:
    """
    Load the raw neighborhoods dataset as a GeoDataFrame.
    """
    if not path.exists():
        raise FileNotFoundError(f"Neighborhoods file not found: {path}")

    logger.info(f"Loading neighborhoods from {path}")
    neigh_gdf = gpd.read_file(path)

    if neigh_gdf.empty:
        raise ValueError(f"Neighborhoods file is empty: {path}")

    if neigh_gdf.crs is None:
        logger.warning(
            "Neighborhoods layer has no CRS set. "
            "You may need to manually set it to match the boundary."
        )

    return neigh_gdf


def align_crs(
    neighborhoods: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Ensure that neighborhoods and boundary share the same CRS.
    Reprojects neighborhoods to the boundary CRS if necessary.
    """
    if boundary.crs is None and neighborhoods.crs is None:
        logger.warning(
            "Both neighborhoods and boundary have no CRS. "
            "Proceeding without reprojection, but this may cause issues."
        )
        return neighborhoods, boundary

    if boundary.crs is None and neighborhoods.crs is not None:
        logger.warning(
            "Boundary CRS is None but neighborhoods has CRS. "
            "Assuming neighborhoods CRS is already correct."
        )
        return neighborhoods, boundary

    if boundary.crs is not None and neighborhoods.crs is None:
        logger.info(
            "Neighborhoods CRS is None; setting it to match boundary CRS."
        )
        neighborhoods = neighborhoods.set_crs(boundary.crs)
        return neighborhoods, boundary

    # Both have CRS defined
    if neighborhoods.crs != boundary.crs:
        logger.info(
            f"Reprojecting neighborhoods from {neighborhoods.crs} to {boundary.crs}"
        )
        neighborhoods = neighborhoods.to_crs(boundary.crs)

    return neighborhoods, boundary


def clip_neighborhoods_to_boundary(
    neighborhoods: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Clip neighborhoods to the city boundary polygon(s).
    """
    logger.info("Clipping neighborhoods to the city boundary")
    clipped = gpd.clip(neighborhoods, boundary)

    if clipped.empty:
        raise ValueError(
            "No neighborhood geometries remain after clipping. "
            "Check that the layers overlap and CRS is correct."
        )

    return clipped


def standardize_neighborhood_names(
    neighborhoods: gpd.GeoDataFrame,
    raw_name_column: str,
    standardized_name_column: str,
) -> gpd.GeoDataFrame:
    """
    Create a standardized neighborhood_name column.

    - Casts to string
    - Strips whitespace
    - Collapses multiple spaces
    - Converts to Title Case
    """
    if raw_name_column not in neighborhoods.columns:
        raise KeyError(
            f"Expected name column '{raw_name_column}' not found in neighborhoods. "
            f"Available columns: {list(neighborhoods.columns)}"
        )

    logger.info(
        f"Standardizing neighborhood names from column '{raw_name_column}' "
        f"to '{standardized_name_column}'"
    )

    # Work on a copy to avoid chained assignment warnings
    neighborhoods = neighborhoods.copy()

    series = neighborhoods[raw_name_column].astype(str)

    # Normalize strings
    series = (
        series.str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    neighborhoods[standardized_name_column] = series

    # Basic sanity check: warn if any names are empty after cleaning
    empty_count = (neighborhoods[standardized_name_column] == "").sum()
    if empty_count > 0:
        logger.warning(
            f"{empty_count} neighborhoods have empty '{standardized_name_column}' "
            "after cleaning. You may want to inspect these."
        )

    return neighborhoods


def select_output_columns(
    neighborhoods: gpd.GeoDataFrame,
    standardized_name_column: str,
) -> gpd.GeoDataFrame:
    """
    Select a clean set of columns to carry forward.

    For now we keep only:
    - standardized_name_column
    - geometry

    You can add more attributes here if needed downstream.
    """
    cols_to_keep = [standardized_name_column, "geometry"]

    # Retain only columns that actually exist
    cols_to_keep = [c for c in cols_to_keep if c in neighborhoods.columns]

    logger.info(f"Selecting output columns: {cols_to_keep}")

    return neighborhoods[cols_to_keep].copy()


# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

def main() -> None:
    logger.info("Starting neighborhood preparation pipeline")

    # Ensure intermediate directory exists
    ensure_directory(OUTPUT_NEIGHBORHOODS_PATH)

    # Load inputs
    boundary_gdf = load_boundary(BOUNDARY_PATH)
    neighborhoods_gdf = load_neighborhoods(RAW_NEIGHBORHOODS_PATH)

    # Align CRS
    neighborhoods_gdf, boundary_gdf = align_crs(neighborhoods_gdf, boundary_gdf)

    # Clip to boundary
    neighborhoods_clipped = clip_neighborhoods_to_boundary(
        neighborhoods_gdf, boundary_gdf
    )

    # Standardize names
    neighborhoods_named = standardize_neighborhood_names(
        neighborhoods_clipped,
        raw_name_column=RAW_NAME_COLUMN,
        standardized_name_column=STANDARDIZED_NAME_COLUMN,
    )

    # Select final columns
    neighborhoods_clean = select_output_columns(
        neighborhoods_named,
        standardized_name_column=STANDARDIZED_NAME_COLUMN,
    )

    # Save to GeoJSON
    logger.info(f"Saving cleaned neighborhoods to {OUTPUT_NEIGHBORHOODS_PATH}")
    neighborhoods_clean.to_file(OUTPUT_NEIGHBORHOODS_PATH, driver="GeoJSON")

    logger.info("Neighborhood preparation completed successfully")


if __name__ == "__main__":
    main()
