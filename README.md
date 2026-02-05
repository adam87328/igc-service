# igc-service

Microservices for paraglider tracklog analysis.

## Services

### xcmetrics (Port 8081)
Processes IGC files and returns GeoJSON with tracklogs split into glides and thermals.

### geolookup (Port 8082)
Geographic lookup services including nearest towns, takeoff locations, and administrative regions.

### xcscore (Port 8083)
Cross-country scoring for paragliding flights.

### dem (Port 8084)
Digital Elevation Model service that adds ground elevation data to GPS coordinates. Works seamlessly with xcmetrics output.

## Running All Services

### Using Docker Compose (Recommended)

Start all services with Docker Compose:
```bash
docker compose up
```

Or run in detached mode:
```bash
docker compose up -d
```

To stop all services:
```bash
docker compose down
```

**Note:** For the DEM service, you need to provide DEM tiles. Set the `DEM_TILES_DIR` environment variable to your DEM tiles directory:
```bash
export DEM_TILES_DIR=/path/to/your/dem_tiles
docker compose up
```

### Running Individual Services

Each service can also be run independently using its own docker-compose file in the service directory:
```bash
cd service/xcmetrics
docker compose up
```
