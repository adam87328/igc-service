# DEM Service Usage Examples

This document provides practical examples for using the updated DEM service.

## Table of Contents
1. [Setup](#setup)
2. [Download Tiles](#download-tiles)
3. [Running the Service](#running-the-service)
4. [API Usage Examples](#api-usage-examples)
5. [Integration Examples](#integration-examples)

---

## Setup

### Prerequisites
- Python 3.12+
- Docker (optional, for containerized deployment)
- AWS CLI (for downloading tiles)

### Install AWS CLI
```bash
# Ubuntu/Debian
sudo apt-get install awscli

# macOS
brew install awscli

# via pip
pip install awscli
```

---

## Download Tiles

### Option 1: Download All Alps Tiles
Download all 78 tiles covering the Alps region (43°N-48°N, 5°E-17°E):

```bash
cd service/dem/downloadDEM
python download.py /data/dem_tiles
```

Expected output:
```
Downloading Copernicus DSM tiles for the Alps region
  Latitude range: 43°N to 48°N
  Longitude range: 5°E to 17°E
  Output directory: /data/dem_tiles

Downloading tile 43°N, 5°E...
  S3 key: Copernicus_DSM_COG_10_N43_00_E005_00_DEM/...
  Output: /data/dem_tiles/Copernicus_DSM_COG_10_N43_00_E005_00_DEM.tif
  ✓ Download successful!
...
Download complete: 78/78 tiles successful
```

### Option 2: Download Single Tile
Download just one tile (e.g., for testing):

```bash
python download.py --tile 47 9 /data/dem_tiles
```

This downloads the tile covering 47°N-48°N, 9°E-10°E.

### Option 3: Download to Default Directory
```bash
python download.py
```

Tiles are saved to `./dem_tiles` in the current directory.

---

## Running the Service

### Development Mode (Standalone)

```bash
cd service/dem

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
cd app
uvicorn main:app --port 8084
```

The service uses the sample tile in `tests/resources/` by default.

### Production Mode (Docker)

#### Build Image
```bash
cd service/dem
docker build -t dem .
```

#### Run with Volume Mount
```bash
docker run -d \
  --name dem-service \
  -p 8084:8084 \
  -v /data/dem_tiles:/data/dem_tiles:ro \
  dem
```

#### Run with Custom Tile Path
```bash
docker run -d \
  --name dem-service \
  -p 8084:8084 \
  -v /mnt/storage/tiles:/app/tiles:ro \
  -e DEM_TILES_DIR=/app/tiles \
  dem
```

#### Using Docker Compose
1. Edit `docker-compose.yml`:
   ```yaml
   volumes:
     - /data/dem_tiles:/data/dem_tiles:ro  # Update this path
   ```

2. Start service:
   ```bash
   docker-compose up -d
   ```

3. Check status:
   ```bash
   docker-compose ps
   docker-compose logs dem
   ```

---

## API Usage Examples

### Health Check
```bash
curl http://localhost:8084/
```

Response:
```json
{"message": "dem"}
```

### Example 1: Single Coordinate
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [
      {"lat": 47.5, "lon": 9.5}
    ]
  }'
```

Response:
```json
{
  "coordinates": [
    {
      "lat": 47.5,
      "lon": 9.5,
      "ground_elevation": 394.0
    }
  ]
}
```

### Example 2: Multiple Coordinates
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [
      {"lat": 47.5, "lon": 9.5},
      {"lat": 47.8, "lon": 9.8},
      {"lat": 46.5, "lon": 8.5}
    ]
  }'
```

Response:
```json
{
  "coordinates": [
    {
      "lat": 47.5,
      "lon": 9.5,
      "ground_elevation": 394.0
    },
    {
      "lat": 47.8,
      "lon": 9.8,
      "ground_elevation": 643.34
    },
    {
      "lat": 46.5,
      "lon": 8.5,
      "ground_elevation": null
    }
  ]
}
```

Note: `null` elevation indicates no tile available for that location.

### Example 3: GeoJSON LineString
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [9.5, 47.5],
            [9.6, 47.6],
            [9.7, 47.7]
          ]
        },
        "properties": {
          "name": "Flight Path"
        }
      }
    ]
  }'
```

Response:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [9.5, 47.5],
          [9.6, 47.6],
          [9.7, 47.7]
        ]
      },
      "properties": {
        "name": "Flight Path",
        "ground_elevation": [394.0, 422.34, 543.21]
      }
    }
  ]
}
```

### Example 4: GeoJSON Point
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [9.5, 47.5]
        },
        "properties": {
          "name": "Takeoff"
        }
      }
    ]
  }'
```

---

## Integration Examples

### Python Client
```python
import requests

# DEM service URL
dem_url = "http://localhost:8084/"

# Get elevation for coordinates
def get_elevations(coordinates):
    response = requests.post(
        dem_url,
        json={"coordinates": coordinates}
    )
    response.raise_for_status()
    return response.json()

# Example usage
coords = [
    {"lat": 47.5, "lon": 9.5},
    {"lat": 47.8, "lon": 9.8}
]

result = get_elevations(coords)
for coord in result["coordinates"]:
    print(f"Lat: {coord['lat']}, Lon: {coord['lon']}, "
          f"Elevation: {coord['ground_elevation']}m")
```

### Python with GeoJSON
```python
import requests

# GeoJSON from xcmetrics
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[9.5, 47.5], [9.6, 47.6]]
            },
            "properties": {"name": "Track"}
        }
    ]
}

# Add elevations
response = requests.post("http://localhost:8084/", json=geojson)
enhanced_geojson = response.json()

# Access elevations
for feature in enhanced_geojson["features"]:
    elevations = feature["properties"]["ground_elevation"]
    print(f"Track elevations: {elevations}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function getElevations(coordinates) {
  const response = await axios.post('http://localhost:8084/', {
    coordinates: coordinates
  });
  return response.data;
}

// Example
const coords = [
  { lat: 47.5, lon: 9.5 },
  { lat: 47.8, lon: 9.8 }
];

getElevations(coords).then(result => {
  result.coordinates.forEach(coord => {
    console.log(`${coord.lat}, ${coord.lon}: ${coord.ground_elevation}m`);
  });
});
```

### Integration with xcmetrics
```python
import requests

# 1. Process IGC file with xcmetrics
with open('flight.igc', 'rb') as f:
    xcmetrics_response = requests.post(
        'http://localhost:8081/',
        files={'file': f}
    )
    xcmetrics_data = xcmetrics_response.json()

# 2. Add ground elevation to glides
glides = xcmetrics_data['glides']
dem_response = requests.post(
    'http://localhost:8084/',
    json=glides
)
enhanced_glides = dem_response.json()

# 3. Add ground elevation to thermals
thermals = xcmetrics_data['thermals']
dem_response = requests.post(
    'http://localhost:8084/',
    json=thermals
)
enhanced_thermals = dem_response.json()

# Now you have elevation data for the entire flight
print(f"Processed {len(enhanced_glides['features'])} glides")
print(f"Processed {len(enhanced_thermals['features'])} thermals")
```

---

## Troubleshooting

### Service Returns null Elevations
**Cause**: No tile available for the requested coordinates.

**Solution**: 
1. Check if tiles cover the area (43°N-48°N, 5°E-17°E for Alps)
2. Download missing tiles:
   ```bash
   python download.py --tile 47 9 /data/dem_tiles
   ```

### Docker Container Can't Read Tiles
**Cause**: Volume not mounted or wrong permissions.

**Solution**:
1. Check volume mount:
   ```bash
   docker inspect dem-service | grep -A 10 Mounts
   ```
2. Verify tiles directory exists and is readable:
   ```bash
   ls -la /data/dem_tiles
   ```

### Service Won't Start
**Cause**: Missing dependencies or port conflict.

**Solution**:
1. Check logs:
   ```bash
   docker logs dem-service
   ```
2. Verify port 8084 is available:
   ```bash
   netstat -tuln | grep 8084
   ```

### Slow Performance
**Cause**: Many coordinates in different tiles.

**Solution**: The service already optimizes by grouping coordinates by tile. For very large batches, consider:
1. Splitting requests into smaller batches
2. Pre-downloading tiles to fast storage (SSD)
3. Increasing Docker memory if needed

---

## Performance Tips

1. **Batch Coordinates**: Send multiple coordinates in one request rather than many single-coordinate requests
2. **Pre-download Tiles**: Download all needed tiles before production use
3. **Use SSD Storage**: Store tiles on fast storage for better read performance
4. **Mount as Read-Only**: Use `:ro` flag to prevent accidental modifications
5. **Monitor Memory**: Each open tile uses memory; service automatically manages cache

---

## Additional Resources

- [Main README](README.md) - Service documentation
- [Download Guide](downloadDEM/README.md) - Detailed download instructions
- [Migration Summary](MIGRATION_SUMMARY.md) - Technical migration details
- [Copernicus DEM Info](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) - Official dataset documentation
