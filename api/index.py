from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel relative pathing
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@app.get("/api/v1/tracts")
async def get_tracts():
    file_path = DATA_DIR / "riverside_tracts_accessibility_15min.geojson"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Tracts data not found")
    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/api/v1/parks")
async def get_parks():
    file_path = DATA_DIR / "parks.geojson"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Parks data not found")
    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/api/v1/neighborhoods")
async def get_neighborhoods():
    file_path = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min_flagged.geojson"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Neighborhoods data not found")
    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/api/v1/stats")
async def get_stats():
    neigh_path = DATA_DIR / "outputs" / "riverside_neighborhoods_accessibility_15min_flagged.geojson"
    if not neigh_path.exists():
        raise HTTPException(status_code=404, detail="Data not found")
    
    with open(neigh_path, "r") as f:
        data = json.load(f)
    
    features = data.get("features", [])
    total_neighs = len(features)
    underserved = sum(1 for f in features if f["properties"].get("is_underserved"))
    
    return {
        "total_neighborhoods": total_neighs,
        "underserved_count": underserved,
        "underserved_percentage": round((underserved / total_neighs) * 100, 1) if total_neighs > 0 else 0
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
