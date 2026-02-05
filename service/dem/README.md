# DEM Microservice

Digital Elevation Model (DEM) microservice that adds ground elevation data to GPS coordinates using Copernicus DSM tiles.

## Overview

This service accepts GeoJSON FeatureCollections or coordinate lists and enriches them with ground elevation data from Copernicus DSM (Digital Surface Model) tiles. It's designed to work seamlessly with the output from the xcmetrics service.

## Features

- Accepts GeoJSON FeatureCollection (from xcmetrics or similar sources)
- Accepts simple coordinate lists
- Supports LineString, Point, and MultiLineString geometries
- Uses Copernicus DSM 30m resolution tiles via rasterio
- Returns enhanced data with `ground_elevation` added to properties
- Configurable tile storage location

## Copernicus DSM Tiles

This service uses the Copernicus Digital Surface Model (DSM) at 30m resolution. Tiles are stored externally on the local filesystem and mounted into the Docker container.

### Downloading Tiles

Use the provided download script to fetch tiles for the Alps region:

```bash
cd downloadDEM
python download.py /path/to/dem_tiles
```

Options:
- `python download.py` - Download all Alps tiles to `./dem_tiles`
- `python download.py /custom/path` - Download to a custom directory
- `python download.py --tile 47 9 /path` - Download a single tile

The script downloads tiles covering the Alps region (43°N-48°N, 5°E-17°E).

### Tile Configuration

The service reads tiles from a configurable directory:

1. **Environment Variable**: Set `DEM_TILES_DIR` to the tiles directory path
2. **Default (Docker)**: `/data/dem_tiles` (should be mounted as a volume)
3. **Default (Development)**: `tests/resources` (contains one sample tile)

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

### Standalone (Development)

For development with the sample tile:
```bash
cd app
uvicorn main:app --port 8084
```

### With Docker

Build the image:
```bash
docker build -t dem .
```

Run with mounted tiles directory:
```bash
docker run -p 8084:8084 -v /path/to/dem_tiles:/data/dem_tiles dem
```

Or with custom DEM_TILES_DIR:
```bash
docker run -p 8084:8084 \
  -v /path/to/dem_tiles:/mnt/tiles \
  -e DEM_TILES_DIR=/mnt/tiles \
  dem
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
- Rasterio: Geospatial raster data I/O
- NumPy: Numerical computations

## Notes

### Copernicus DSM Data
- 30m resolution Digital Surface Model
- Tiles are 1°x1° (latitude x longitude)
- Stored in Cloud-Optimized GeoTIFF (COG) format
- Available from AWS S3 public bucket (no credentials required)
- The service expects tiles to be pre-downloaded to a local directory

### Tile Naming Convention
Tiles follow the Copernicus naming convention:
```
Copernicus_DSM_COG_10_N47_00_E009_00_DEM.tif
```
Where N47 and E009 represent the lower-left corner of the tile.

### Coordinate Format
- Input coordinates use standard WGS84 (EPSG:4326)
- GeoJSON uses [longitude, latitude] order (per GeoJSON spec)
- Coordinate list uses {"lat": ..., "lon": ...} format

### Elevation Accuracy
- Copernicus DSM provides 30m resolution
- Accuracy varies by terrain type and data quality
- DSM represents surface elevation (includes vegetation, buildings)
- For bare earth elevation, consider using Copernicus DTM (Digital Terrain Model)

## Port

Default port: **8084**
