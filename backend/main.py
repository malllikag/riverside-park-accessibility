from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# define paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = BASE_DIR / "analysis"

# Mount data directory to serve GeoJSON/files if needed
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

@app.get("/")
async def read_root():
    # Serve the main visualization map
    map_path = BASE_DIR / "riverside_accessibility_map.html"
    if map_path.exists():
        return FileResponse(map_path)
    return {"message": "Map file not found. Please run the analysis scripts first."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
