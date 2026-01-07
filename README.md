# Riverside County Parks Accessibility Analysis

This project analyzes park accessibility in Riverside, California, using OpenStreetMap data, census tracts, and isochrone calculations. It provides a visualization of accessibility scores across different neighborhoods and census tracts.

## Project Structure

- `analysis/`: Python scripts for data downloading, processing, and visualization.
- `backend/`: FastAPI server for serving the generated accessibility map.
- `data/`: (Not tracked in Git) Directory where GeoJSON and other geo-spatial files are stored.

## Setup and Installation

### Prerequisites
- Python 3.10+
- `pip`

### Step 1: Install Dependencies
Navigate to the root directory and install the required packages:

```bash
pip install -r backend/requirements.txt
```

*(Optional)* If you are running the analysis scripts, ensure you have the analysis requirements installed (standard geospatial libraries like `osmnx`, `geopandas`, `folium`, etc.).

## Data Analysis Pipeline

To regenerate the analysis, run the scripts in the `analysis/` directory in the following order:

1.  **`01_download_data.py`**: Downloads the city boundary, walking network, and park features from OpenStreetMap.
2.  **`02_generate_isochrones.py`**: Calculates 15-minute walking isochrones for all identified parks.
3.  **`03_prepare_tracts.py`**: Downloads and prepares US Census tracts for the Riverside area.
4.  **`04_compute_tract_accessibility.py`**: Calculates accessibility scores for each census tract based on park proximity.
5.  **`05_prepare_neighborhoods.py`**: Processes neighborhood-level data for the analysis.
6.  **`06_compute_neighborhood_accessibility.py`**: Aggregates tract-level data to the neighborhood level.
7.  **`07_flag_underserved.py`**: Identifies neighborhoods with low accessibility scores.
8.  **`08_visualize_results.py`**: Generates the final `riverside_accessibility_map.html`.

## Running the Web Application

The project now features a modern React-based dashboard. To run the full application (Frontend + Backend):

### 1. Start the Backend API
Navigate to the `backend/` directory and run the server:
```bash
cd backend
python main.py
```
The API will be available at `http://localhost:8000`.

### 2. Start the Frontend Dashboard
Navigate to the `frontend/` directory and start the development server:
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

## Data Analysis Pipeline
...
MIT
