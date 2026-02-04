# DEM Microservice

Digital Elevation Model (DEM) microservice that adds ground elevation data to GPS coordinates.

## Overview

This service accepts GeoJSON FeatureCollections or coordinate lists and enriches them with ground elevation data. It's designed to work seamlessly with the output from the xcmetrics service.

## Features

- Accepts GeoJSON FeatureCollection (from xcmetrics or similar sources)
- Accepts simple coordinate lists
- Supports LineString, Point, and MultiLineString geometries
- Uses SRTM elevation data (with estimation fallback)
- Returns enhanced data with `ground_elevation` added to properties

## API Endpoints

### GET /
Health check endpoint.

**Response:**
```json
{"message": "dem"}
```

### POST /
Add ground elevation data to coordinates.

**Input Format 1 - GeoJSON FeatureCollection:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], [lon, lat], ...]
      },
      "properties": {
        "name": "Flight track"
      }
    }
  ]
}
```

**Input Format 2 - Coordinate List:**
```json
{
  "coordinates": [
    {"lat": 45.9237, "lon": 6.8694},
    {"lat": 45.8326, "lon": 6.8652}
  ]
}
```

**Response (GeoJSON):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {...},
      "properties": {
        "name": "Flight track",
        "ground_elevation": [1028.3, 1046.9, ...]
      }
    }
  ]
}
```

**Response (Coordinate List):**
```json
{
  "coordinates": [
    {"lat": 45.9237, "lon": 6.8694, "ground_elevation": 1028.3},
    {"lat": 45.8326, "lon": 6.8652, "ground_elevation": 1046.9}
  ]
}
```

## Usage with xcmetrics

The DEM service is designed to work with xcmetrics output:

```python
import requests

# 1. Get xcmetrics data
with open('flight.igc', 'rb') as f:
    response = requests.post('http://localhost:8081/', files={'file': f})
    xcmetrics_data = response.json()

# 2. Add ground elevation to glides
glides = xcmetrics_data['glides']
response = requests.post('http://localhost:8084/', json=glides)
enhanced_glides = response.json()

# 3. Add ground elevation to thermals
thermals = xcmetrics_data['thermals']
response = requests.post('http://localhost:8084/', json=thermals)
enhanced_thermals = response.json()
```

## Running the Service

### Standalone
```bash
cd app
uvicorn main:app --port 8084
```

### With Docker
```bash
docker build -t dem .
docker run -p 8084:8084 dem
```

### With tmux (all services)
```bash
cd ..
./run_tmux.sh
```

## Testing

```bash
./run_tests.sh
```

Or manually:
```bash
python3 -m unittest tests/tests.py
```

## Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- srtm.py: SRTM elevation data access

## Notes

### SRTM Data
The service uses SRTM (Shuttle Radar Topography Mission) data for elevation lookup. In production environments:
- Pre-download SRTM data tiles for your region
- Or use a local DEM data source
- The service includes an estimation fallback when SRTM data is unavailable

### Coordinate Format
- Input coordinates use standard WGS84 (EPSG:4326)
- GeoJSON uses [longitude, latitude] order (per GeoJSON spec)
- Coordinate list uses {"lat": ..., "lon": ...} format

### Elevation Accuracy
- SRTM provides ~30-90m resolution depending on location
- Accuracy varies by terrain type and data availability
- The estimation fallback provides rough approximations for testing

## Port

Default port: **8084**
