# 🌳 Riverside County Parks Accessibility Dashboard (v2.0)

A professional-grade urban planning and geospatial analytics dashboard designed to measure and visualize park accessibility (the "15-minute city" model) across Riverside County, CA.

---

## 📍 Project Overview

This tool identifies **"Park Deserts"** by simulating realistic 15-minute walking routes from every home in Riverside to the nearest public park. It uses high-fidelity street-network modeling to provide scientifically accurate accessibility scores (0-100).

### **Key Features**
- **V2 High-Accuracy Model**: Uses Multi-Entrance sampling and street-accurate concave reachability buffers.
- **Interactive Heatmap**: Visualizes accessibility layers (Census Tracts & Neighborhoods).
- **Personal Search**: Users can input their address to instantly receive a personalized accessibility score.
- **Top 5 Chart**: Real-time ranking of the most walkable neighborhoods in the county.

---

## 🏗️ The Technical Workflow

The project is built as a three-layer "Engine" that converts raw geographic data into a user-friendly dashboard.

### **1. Data Mining & Cleaning**
*   **OSMNX**: *Map Data Downloader.* (Pulls real-world street and park coordinates).
*   **Python**: *Execution Engine.* (The core code that automates the whole process).

### **2. Geospatial Logic (The Math)**
*   **Dijkstra's Algorithm**: *Pathfinding Logic.* (Calculates the shortest walking route through millions of intersections).
*   **NetworkX**: *Graph Math Library.* (Industry-standard tool for networking/transportation math).
*   **GeoPandas**: *Spatial Database.* (Handles massive tables of map shapes and coordinates).
*   **Shapely**: *Geometry Engine.* (Calculates intersections, areas, and boundaries on the map).

### **3. Full-Stack Web App**
*   **FastAPI**: *High-Speed Backend.* (Serves data from the Python engine to the browser).
*   **React 19**: *User Interface.* (Builds the interactive widgets and buttons).
*   **Leaflet**: *Mapping Engine.* (Renders the colorful heatmap in your browser).
*   **Nominatim**: *Address Finder.* (Converts your typed address into Map Coordinates).
*   **Turf.js**: *Browser-based Spatial Engine.* (Calculates your personal score instantly in the browser).

---

## 📂 Project Structure

- `analysis/`: High-fidelity Python scripts for data extraction and isochrone calculation.
- `api/`: FastAPI backend (optimized for Vercel Serverless deployment).
- `frontend/`: React-based dashboard with mobile-responsive design.
- `data/`: GeoJSON results and street-network graphs.

---

## 🚀 Setup & Local Running

### **Prerequisites**
- Python 3.10+
- Node.js & npm

### **1. Setup Architecture**
From the root directory:
```bash
# Install frontend dependencies
npm install --prefix frontend

# Install backend dependencies
pip install -r api/requirements.txt
```

### **2. Run Locally**
Open two terminals:

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

---

## 📈 The Accessibility Formula (V2)
The score (0-100) represents the **percentage of residential land** within a 15-minute walk of a park entrance. 
- **Multi-Entrance**: Analysis starts from every gate/sidewalk of a park.
- **Network-Based**: We only count distance traveled on official roads and trails, not "as the crow flies."

---
*Developed for Riverside County Geospatial Analytics.*
