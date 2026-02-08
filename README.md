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

## Production Ready for Celery/Redis Queues

These microservices are designed to handle background traffic from **Celery task queues** with Redis as a broker. Each service runs with **Gunicorn + Uvicorn workers** in production mode, providing:

- **Multiple worker processes** for parallel request handling
- **Configurable concurrency** via environment variables
- **Graceful restarts** and worker management
- **Health checks** for monitoring and orchestration

### Quick Start for Production

```bash
# Production deployment with optimized settings
docker compose up -d

# Scale specific services for higher load
docker compose up -d --scale xcmetrics=3

# View logs
docker compose logs -f
```

### Configuration for High-Volume Processing

Set environment variables to tune for your workload:

```bash
# .env file
WORKERS=6                    # Number of worker processes per container
WORKER_CONNECTIONS=1500      # Max concurrent connections per worker
TIMEOUT=180                  # Request timeout in seconds
LOG_LEVEL=info

# For DEM service
DEM_TILES_DIR=/path/to/dem_tiles
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment guide including:
- Worker count recommendations
- Scaling strategies
- Performance tuning
- Celery integration best practices

## Documentation

- **[API_GUIDE.md](API_GUIDE.md)** - Complete API reference with batch processing patterns and Celery task examples
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide with Docker, scaling, and performance tuning
- **[service/dem/README.md](service/dem/README.md)** - Detailed DEM service documentation

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

## Testing

### Integration Tests

Run the integration test to verify the full xcmetrics → DEM workflow:

```bash
# Make sure services are running
docker compose up -d

# Run integration test
python test/test_integration.py
```

### Batch Testing

Test concurrent request handling (simulates Celery queue processing):

```bash
# Test all services with 10 concurrent requests
python test/batch_test.py

# Test with higher concurrency
python test/batch_test.py --concurrency 20

# Test specific service
python test/batch_test.py --service xcmetrics --concurrency 15
```

The batch test script validates:
- Concurrent request handling
- Response times under load
- Error rates
- Overall throughput

### Individual Service Tests

Each service has its own test suite:

```bash
# xcmetrics tests
cd service/xcmetrics
./run_tests.sh

# DEM tests
cd service/dem
./run_tests.sh

# Similar for other services
```

## API Quick Reference

### xcmetrics: POST /

Upload an IGC file and get flight metrics:

```bash
curl -X POST http://localhost:8081/ \
  -F "file=@flight.igc"
```

### dem: POST /

Add terrain elevation to track points:

```bash
curl -X POST http://localhost:8084/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_points": [
      {
        "timestamp": "2024-08-15T10:23:45Z",
        "lat": 47.5,
        "lon": 9.5,
        "gps_alt": 1523
      }
    ]
  }'
```

### geolookup: GET /nearest_town

Find nearest town:

```bash
curl "http://localhost:8082/nearest_town?lat=47.5&lon=9.5"
```

### geolookup: GET /takeoffdb

Find nearby takeoff locations:

```bash
curl "http://localhost:8082/takeoffdb?lat=47.5&lon=9.5&radius=1000"
```

### xcscore: POST /

Score a cross-country flight:

```bash
curl -X POST http://localhost:8083/ \
  -F "file=@flight.igc"
```

See [API_GUIDE.md](API_GUIDE.md) for complete API documentation with batch processing examples.

## Celery Integration Example

```python
from celery import Celery
import requests

app = Celery('tasks', broker='redis://localhost:6379/0')

# Configure connection pooling for efficiency
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20
)
session.mount('http://', adapter)

@app.task(bind=True, max_retries=3)
def process_igc_file(self, file_path):
    """Process IGC file using xcmetrics service"""
    try:
        with open(file_path, 'rb') as f:
            response = session.post(
                'http://xcmetrics:8081/',
                files={'file': f},
                timeout=120
            )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

See [API_GUIDE.md](API_GUIDE.md) for more comprehensive Celery examples including:
- Connection pooling
- Batch processing
- Task pipelines
- Error handling
- Rate limiting

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Celery Workers                        │
│              (Django/Redis Backend)                     │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP Requests
                  ├──────────────┬──────────────┬──────────
                  ▼              ▼              ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │  xcmetrics   │ │  geolookup   │ │    xcscore   │
         │   :8081      │ │   :8082      │ │   :8083      │
         └──────┬───────┘ └──────────────┘ └──────────────┘
                │
                ▼ track_points
         ┌──────────────┐
         │     dem      │
         │   :8084      │
         └──────────────┘
```

## Performance Characteristics

| Service | Avg Response Time | Recommended Workers | Notes |
|---------|------------------|-------------------|-------|
| xcmetrics | 2-10s | 4-8 | CPU-intensive processing |
| geolookup | 50-200ms | 2-4 | Fast database lookups |
| xcscore | 1-5s | 4-8 | CPU-intensive scoring |
| dem | 1-5s | 4-8 | I/O-bound raster lookups |

**Throughput**: With default configuration (4 workers), each service can handle:
- xcmetrics/xcscore: ~10-20 requests/second
- geolookup: ~50-100 requests/second
- dem: ~20-30 requests/second

Scale horizontally (multiple containers) for higher throughput.

## Health Checks

All services expose health check endpoints at `GET /`:

```bash
# Check if services are running
curl http://localhost:8081/  # xcmetrics
curl http://localhost:8082/  # geolookup
curl http://localhost:8083/  # xcscore
curl http://localhost:8084/  # dem
```

Health checks are configured in `docker-compose.yml` for automatic monitoring and restart.

## Development

For local development without Docker:

```bash
# Install dependencies
cd service/xcmetrics
pip install -r requirements.txt

# Run with hot reload
fastapi dev app/main.py --port 8081
```

For production deployment, the Docker images automatically use Gunicorn with multiple workers.

## License

See [LICENSE](LICENSE) file for details.
