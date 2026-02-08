# Deployment Guide for Production

This guide covers deploying the igc-service microservices for production workloads, including handling background traffic from Celery task queues.

## Table of Contents

- [Overview](#overview)
- [Production Configuration](#production-configuration)
- [Docker Deployment](#docker-deployment)
- [Scaling and Load Balancing](#scaling-and-load-balancing)
- [Performance Tuning](#performance-tuning)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Best Practices for Celery Integration](#best-practices-for-celery-integration)

## Overview

All microservices use **Gunicorn** with **Uvicorn workers** in production mode, providing:
- Multiple worker processes for parallel request handling
- Graceful restarts and worker management
- Process-level isolation for stability
- Automatic worker recycling for memory management

### Services Architecture

| Service | Port | Purpose | Recommended Workers |
|---------|------|---------|-------------------|
| **xcmetrics** | 8081 | IGC file processing | 4-8 (CPU-intensive) |
| **geolookup** | 8082 | Geographic lookups | 2-4 (I/O-bound) |
| **xcscore** | 8083 | Flight scoring | 4-8 (CPU-intensive) |
| **dem** | 8084 | Elevation data | 4-8 (I/O-bound) |

## Production Configuration

### Environment Variables

Each service supports the following environment variables for production tuning:

```bash
# Number of worker processes (default: 4)
# Recommended: 2-4 × CPU cores for CPU-bound tasks
# Recommended: 1-2 × CPU cores for I/O-bound tasks
WORKERS=4

# Worker class (default: uvicorn.workers.UvicornWorker)
WORKER_CLASS=uvicorn.workers.UvicornWorker

# Maximum concurrent connections per worker (default: 1000)
WORKER_CONNECTIONS=1000

# Request timeout in seconds (default: 120)
# Increase for long-running IGC processing
TIMEOUT=120

# Keep-alive timeout in seconds (default: 5)
KEEPALIVE=5

# Log level (default: info)
LOG_LEVEL=info
```

### Recommended Configurations

#### For Light Traffic (< 10 requests/sec)
```bash
WORKERS=2
WORKER_CONNECTIONS=500
TIMEOUT=120
```

#### For Medium Traffic (10-50 requests/sec)
```bash
WORKERS=4
WORKER_CONNECTIONS=1000
TIMEOUT=120
```

#### For Heavy Traffic (> 50 requests/sec)
```bash
WORKERS=8
WORKER_CONNECTIONS=2000
TIMEOUT=180
```

#### For Celery Background Processing
```bash
# Optimized for batch processing with multiple Celery workers
WORKERS=6
WORKER_CONNECTIONS=1500
TIMEOUT=180
KEEPALIVE=10
```

## Docker Deployment

### Single Service Deployment

Deploy a single service with custom configuration:

```bash
# Build the image
cd service/xcmetrics
docker build -t xcmetrics:latest .

# Run with production settings
docker run -d \
  --name xcmetrics \
  -p 8081:8081 \
  -e WORKERS=6 \
  -e WORKER_CONNECTIONS=1500 \
  -e TIMEOUT=180 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  --memory=2g \
  --cpus=4 \
  xcmetrics:latest
```

### Docker Compose Deployment

The provided `docker-compose.yml` runs all services with default production settings:

```bash
# Start all services in production mode
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

#### Override Environment Variables

Create a `.env` file in the root directory:

```bash
# .env file
WORKERS=6
WORKER_CONNECTIONS=1500
TIMEOUT=180
LOG_LEVEL=info
DEM_TILES_DIR=/path/to/your/dem_tiles
```

Then reference in `docker-compose.yml`:

```yaml
services:
  xcmetrics:
    build: ./service/xcmetrics
    environment:
      - WORKERS=${WORKERS:-4}
      - WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}
      - TIMEOUT=${TIMEOUT:-120}
      - LOG_LEVEL=${LOG_LEVEL:-info}
```

## Scaling and Load Balancing

### Horizontal Scaling with Docker Compose

Scale individual services to multiple containers:

```bash
# Scale xcmetrics to 3 replicas
docker compose up -d --scale xcmetrics=3

# Scale multiple services
docker compose up -d --scale xcmetrics=3 --scale dem=2
```

**Note**: When scaling, you'll need to use a reverse proxy (nginx, traefik) to load balance across replicas.

### Example Nginx Configuration

```nginx
upstream xcmetrics_backend {
    least_conn;
    server xcmetrics_1:8081;
    server xcmetrics_2:8081;
    server xcmetrics_3:8081;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://xcmetrics_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
        proxy_read_timeout 180s;
    }
}
```

### Kubernetes Deployment

For Kubernetes deployments, use Horizontal Pod Autoscaler (HPA):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: xcmetrics-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: xcmetrics
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Performance Tuning

### Worker Count Calculation

```python
# For CPU-bound tasks (xcmetrics, xcscore)
workers = (2 × CPU_cores) + 1

# For I/O-bound tasks (geolookup, dem)
workers = (1 × CPU_cores) + 1

# Example: 4 CPU cores
# CPU-bound: 9 workers
# I/O-bound: 5 workers
```

### Memory Considerations

Each worker consumes memory. Monitor and adjust based on available RAM:

```bash
# Check memory usage
docker stats xcmetrics

# Set memory limits in docker-compose.yml
services:
  xcmetrics:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Request Timeout Tuning

Different endpoints may require different timeout values:

- **xcmetrics**: 120-180s (IGC processing can be slow for large files)
- **xcscore**: 90-120s (scoring computation)
- **dem**: 60-90s (raster lookups can be slow)
- **geolookup**: 30-60s (database queries are fast)

## Monitoring and Health Checks

### Health Check Endpoints

All services expose a health check endpoint at `GET /`:

```bash
# Check service health
curl http://localhost:8081/

# Response
{"message": "xcmetrics"}
```

### Docker Health Checks

Health checks are configured in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### Monitoring Metrics

Key metrics to monitor:

1. **Request Rate**: Requests per second per service
2. **Response Time**: Average and P95/P99 latency
3. **Error Rate**: 4xx and 5xx errors per service
4. **Worker Utilization**: CPU and memory per worker
5. **Queue Length**: If using a reverse proxy

### Logging

All services log to stdout/stderr. Configure log aggregation:

```bash
# View logs from all services
docker compose logs -f

# View logs from specific service
docker compose logs -f xcmetrics

# Filter by log level
docker compose logs -f | grep ERROR
```

## Best Practices for Celery Integration

### 1. Connection Pooling

Reuse HTTP connections from Celery tasks:

```python
import requests
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

# Create a session for connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)
session.mount('http://', adapter)

@app.task
def process_igc_file(file_path):
    """Process IGC file using xcmetrics service"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = session.post(
            'http://xcmetrics:8081/',
            files=files,
            timeout=120
        )
    return response.json()
```

### 2. Rate Limiting in Celery

Limit task execution rate to avoid overwhelming services:

```python
@app.task(rate_limit='10/m')  # 10 tasks per minute
def process_igc_file(file_path):
    """Rate-limited IGC processing"""
    # ... implementation
```

### 3. Retry Logic

Implement retry logic for transient failures:

```python
@app.task(
    bind=True,
    autoretry_for=(requests.exceptions.RequestException,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True
)
def process_igc_file(self, file_path):
    """IGC processing with automatic retries"""
    # ... implementation
```

### 4. Batch Processing

Process multiple files in a batch to reduce overhead:

```python
@app.task
def process_batch(file_paths):
    """Process multiple IGC files in parallel"""
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(process_single_file, path)
            for path in file_paths
        ]
        results = [f.result() for f in futures]
    
    return results
```

### 5. Task Prioritization

Use Celery routing to prioritize critical tasks:

```python
# High priority queue for real-time processing
@app.task(queue='high_priority')
def process_urgent_flight(file_path):
    # ... implementation

# Low priority queue for batch processing
@app.task(queue='low_priority')
def process_batch_flight(file_path):
    # ... implementation
```

### 6. Monitoring Celery Tasks

Track task execution and service health:

```python
from celery.signals import task_success, task_failure
import logging

logger = logging.getLogger(__name__)

@task_success.connect
def task_success_handler(sender=None, **kwargs):
    logger.info(f"Task {sender.name} completed successfully")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    logger.error(f"Task {sender.name} failed: {exception}")
```

### 7. Error Handling

Gracefully handle service errors:

```python
@app.task
def process_igc_file(file_path):
    """Process IGC file with error handling"""
    try:
        response = session.post(
            'http://xcmetrics:8081/',
            files={'file': open(file_path, 'rb')},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout processing {file_path}")
        raise  # Retry
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            # Bad request - don't retry
            logger.error(f"Invalid file {file_path}: {e}")
            return {"error": "invalid_file"}
        else:
            # Server error - retry
            raise
    
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        raise
```

## Development vs Production

### Development Mode

For local development, use the FastAPI CLI:

```bash
# Run without Docker
cd service/xcmetrics/app
fastapi dev main.py --port 8081

# Or override Docker command
docker run -it xcmetrics fastapi dev app/main.py --port 8081
```

### Production Mode (Default)

The default Docker command uses Gunicorn with Uvicorn workers:

```bash
# Production command (in Dockerfile)
CMD gunicorn app.main:app \
    --bind 0.0.0.0:8081 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120
```

## Security Considerations

### 1. Network Isolation

Use Docker networks to isolate services:

```yaml
services:
  xcmetrics:
    networks:
      - internal
  
  nginx:
    networks:
      - internal
      - external

networks:
  internal:
    internal: true
  external:
```

### 2. Resource Limits

Always set resource limits in production:

```yaml
services:
  xcmetrics:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 2G
```

### 3. Read-Only Filesystems

Mount volumes as read-only when possible:

```yaml
services:
  dem:
    volumes:
      - ${DEM_TILES_DIR}:/data/dem_tiles:ro  # read-only
```

### 4. Non-Root User

Consider running containers as non-root user for enhanced security.

## Troubleshooting

### High CPU Usage

- Reduce `WORKERS` count
- Check for infinite loops in code
- Profile with `py-spy` or similar tools

### High Memory Usage

- Reduce `WORKERS` count
- Check for memory leaks
- Implement worker recycling: `--max-requests 1000`

### Slow Response Times

- Increase `WORKERS` count
- Check database/file I/O performance
- Use async operations where possible
- Implement caching for repeated requests

### Connection Timeouts

- Increase `TIMEOUT` setting
- Check network connectivity
- Verify health check endpoints

### Worker Crashes

- Check logs: `docker compose logs -f`
- Increase memory limits
- Fix application errors
- Implement proper exception handling

## Summary

For Celery/Redis integration, the recommended production setup is:

1. **Deploy with Docker Compose** using production-tuned settings
2. **Configure 4-8 workers** per service depending on load
3. **Implement connection pooling** in Celery tasks
4. **Add retry logic** with exponential backoff
5. **Monitor health checks** and service metrics
6. **Scale horizontally** when needed using container orchestration

This setup ensures the microservices can handle high-volume background traffic from Celery task queues efficiently and reliably.
