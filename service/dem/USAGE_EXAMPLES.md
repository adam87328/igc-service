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

### Example 1: Single Track Point
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_points": [
      {
        "timestamp": "2024-08-15T10:23:45Z",
        "lat": 47.5,
        "lon": 9.5,
        "gps_alt": 1523,
        "pressure_alt": 1520,
        "segment_type": "glide",
        "segment_id": 0
      }
    ]
  }'
```

Response:
```json
{
  "track_points": [
    {
      "timestamp": "2024-08-15T10:23:45Z",
      "lat": 47.5,
      "lon": 9.5,
      "gps_alt": 1523,
      "pressure_alt": 1520,
      "segment_type": "glide",
      "segment_id": 0,
      "terrain_alt": 394.0
    }
  ]
}
```

### Example 2: Multiple Track Points
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_points": [
      {
        "timestamp": "2024-08-15T10:23:45Z",
        "lat": 47.5,
        "lon": 9.5,
        "gps_alt": 1523,
        "segment_type": "glide",
        "segment_id": 0
      },
      {
        "timestamp": "2024-08-15T10:23:50Z",
        "lat": 47.8,
        "lon": 9.8,
        "gps_alt": 1650,
        "segment_type": "thermal",
        "segment_id": 1
      },
      {
        "timestamp": "2024-08-15T10:23:55Z",
        "lat": 46.5,
        "lon": 8.5,
        "segment_type": "glide",
        "segment_id": 0
      }
    ]
  }'
```

Response:
```json
{
  "track_points": [
    {
      "timestamp": "2024-08-15T10:23:45Z",
      "lat": 47.5,
      "lon": 9.5,
      "gps_alt": 1523,
      "segment_type": "glide",
      "segment_id": 0,
      "terrain_alt": 394.0
    },
    {
      "timestamp": "2024-08-15T10:23:50Z",
      "lat": 47.8,
      "lon": 9.8,
      "gps_alt": 1650,
      "segment_type": "thermal",
      "segment_id": 1,
      "terrain_alt": 643.34
    },
    {
      "timestamp": "2024-08-15T10:23:55Z",
      "lat": 46.5,
      "lon": 8.5,
      "segment_type": "glide",
      "segment_id": 0,
      "terrain_alt": null
    }
  ]
}
```

Note: `null` terrain_alt indicates no tile available for that location.

### Example 3: Minimal Track Points (Only Required Fields)
```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_points": [
      {
        "timestamp": "2024-08-15T10:23:45Z",
        "lat": 47.5,
        "lon": 9.5
      }
    ]
  }'
```

Response:
```json
{
  "track_points": [
    {
      "timestamp": "2024-08-15T10:23:45Z",
      "lat": 47.5,
      "lon": 9.5,
      "terrain_alt": 394.0
    }
  ]
}
```

---

## Integration Examples

### Python Client
```python
import requests

# DEM service URL
dem_url = "http://localhost:8084/"

# Get terrain elevation for track points
def get_terrain_elevations(track_points):
    response = requests.post(
        dem_url,
        json={"track_points": track_points}
    )
    response.raise_for_status()
    return response.json()

# Example usage
track_points = [
    {
        "timestamp": "2024-08-15T10:23:45Z",
        "lat": 47.5,
        "lon": 9.5,
        "gps_alt": 1523,
        "segment_type": "glide",
        "segment_id": 0
    },
    {
        "timestamp": "2024-08-15T10:23:50Z",
        "lat": 47.8,
        "lon": 9.8,
        "gps_alt": 1650,
        "segment_type": "thermal",
        "segment_id": 1
    }
]

result = get_terrain_elevations(track_points)
for point in result["track_points"]:
    print(f"Time: {point['timestamp']}, "
          f"Lat: {point['lat']}, Lon: {point['lon']}, "
          f"GPS Alt: {point.get('gps_alt', 'N/A')}m, "
          f"Terrain Alt: {point['terrain_alt']}m")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function getTerrainElevations(trackPoints) {
  const response = await axios.post('http://localhost:8084/', {
    track_points: trackPoints
  });
  return response.data;
}

// Example
const trackPoints = [
  {
    timestamp: "2024-08-15T10:23:45Z",
    lat: 47.5,
    lon: 9.5,
    gps_alt: 1523,
    segment_type: "glide",
    segment_id: 0
  },
  {
    timestamp: "2024-08-15T10:23:50Z",
    lat: 47.8,
    lon: 9.8,
    gps_alt: 1650,
    segment_type: "thermal",
    segment_id: 1
  }
];

getTerrainElevations(trackPoints).then(result => {
  result.track_points.forEach(point => {
    console.log(`${point.timestamp}: ${point.lat}, ${point.lon} - Terrain: ${point.terrain_alt}m`);
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

# 2. Add terrain elevation to track points
track_points_data = {"track_points": xcmetrics_data['track_points']}
dem_response = requests.post(
    'http://localhost:8084/',
    json=track_points_data
)
enhanced_data = dem_response.json()

# Now you have terrain elevation data for the entire flight
print(f"Processed {len(enhanced_data['track_points'])} track points")
for point in enhanced_data['track_points']:
    terrain_clearance = None
    if point.get('gps_alt') and point.get('terrain_alt'):
        terrain_clearance = point['gps_alt'] - point['terrain_alt']
    print(f"  {point['timestamp']}: Clearance = {terrain_clearance}m")
```

---

## Troubleshooting

### Service Returns null terrain_alt
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
**Cause**: Many track points in different tiles.

**Solution**: The service already optimizes by grouping coordinates by tile. For very large batches, consider:
1. Splitting requests into smaller batches
2. Pre-downloading tiles to fast storage (SSD)
3. Increasing Docker memory if needed

---

## Performance Tips

1. **Batch Track Points**: Send multiple track points in one request rather than many single-point requests
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
