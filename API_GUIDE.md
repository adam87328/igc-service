# API Guide for Batch Processing

This guide provides detailed information on using the igc-service APIs for batch processing from Celery tasks or other automated systems.

## Table of Contents

- [Quick Start](#quick-start)
- [Services Overview](#services-overview)
- [Common Patterns](#common-patterns)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)
- [Example Implementations](#example-implementations)

## Quick Start

### Basic Request Flow

```python
import requests

# 1. Process IGC file
with open('flight.igc', 'rb') as f:
    response = requests.post('http://localhost:8081/', files={'file': f})
    data = response.json()

# 2. Add terrain elevation
track_points = {"track_points": data['track_points']}
response = requests.post('http://localhost:8084/', json=track_points)
enhanced_data = response.json()

# 3. Get geographic info
first_point = data['track_points'][0]
response = requests.get(
    'http://localhost:8082/nearest_town',
    params={'lat': first_point['lat'], 'lon': first_point['lon']}
)
location = response.json()
```

### Celery Task Example

```python
from celery import Celery
import requests

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def process_flight(self, igc_file_path):
    """Process a paraglider flight IGC file"""
    try:
        # Process with xcmetrics
        with open(igc_file_path, 'rb') as f:
            response = requests.post(
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

## Services Overview

### xcmetrics (Port 8081)

**Purpose**: Process IGC files and extract flight metrics
**Input**: IGC file upload
**Output**: Flight summary, glides, thermals, track points

**Typical Processing Time**: 2-10 seconds depending on flight duration
**Recommended Timeout**: 120 seconds
**Rate Limit Recommendation**: 10-20 requests/second per worker

### geolookup (Port 8082)

**Purpose**: Geographic lookups (towns, takeoffs, regions)
**Input**: Latitude/longitude coordinates
**Output**: Geographic information

**Typical Processing Time**: 50-200ms
**Recommended Timeout**: 30 seconds
**Rate Limit Recommendation**: 50-100 requests/second per worker

### xcscore (Port 8083)

**Purpose**: Cross-country flight scoring
**Input**: IGC file upload
**Output**: Flight score and details

**Typical Processing Time**: 1-5 seconds
**Recommended Timeout**: 90 seconds
**Rate Limit Recommendation**: 10-20 requests/second per worker

### dem (Port 8084)

**Purpose**: Add terrain elevation to GPS coordinates
**Input**: Array of track points
**Output**: Track points with terrain altitude

**Typical Processing Time**: 1-5 seconds (depends on point count)
**Recommended Timeout**: 90 seconds
**Rate Limit Recommendation**: 20-30 requests/second per worker

## Common Patterns

### Pattern 1: Full Flight Analysis Pipeline

Complete analysis of a flight from IGC file:

```python
def analyze_flight(igc_file_path):
    """
    Complete flight analysis pipeline:
    1. Extract metrics (xcmetrics)
    2. Add terrain elevation (dem)
    3. Score flight (xcscore)
    4. Get takeoff location (geolookup)
    """
    results = {}
    
    # Step 1: Extract metrics
    with open(igc_file_path, 'rb') as f:
        response = requests.post('http://xcmetrics:8081/', files={'file': f})
        response.raise_for_status()
        results['metrics'] = response.json()
    
    # Step 2: Add terrain elevation
    track_points = {"track_points": results['metrics']['track_points']}
    response = requests.post('http://dem:8084/', json=track_points)
    response.raise_for_status()
    results['terrain'] = response.json()
    
    # Step 3: Score flight
    with open(igc_file_path, 'rb') as f:
        response = requests.post('http://xcscore:8083/', files={'file': f})
        response.raise_for_status()
        results['score'] = response.json()
    
    # Step 4: Get takeoff location
    first_point = results['metrics']['track_points'][0]
    response = requests.get(
        'http://geolookup:8082/takeoffdb',
        params={
            'lat': first_point['lat'],
            'lon': first_point['lon'],
            'radius': 1000  # meters
        }
    )
    response.raise_for_status()
    results['takeoff'] = response.json()
    
    return results
```

### Pattern 2: Batch Processing with Connection Pooling

Efficiently process multiple flights:

```python
import requests
from concurrent.futures import ThreadPoolExecutor

# Create session for connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20,
    pool_maxsize=40,
    max_retries=3
)
session.mount('http://', adapter)

def process_single_flight(igc_file_path):
    """Process a single flight with connection pooling"""
    with open(igc_file_path, 'rb') as f:
        response = session.post(
            'http://xcmetrics:8081/',
            files={'file': f},
            timeout=120
        )
    return response.json()

def process_batch(igc_file_paths, max_workers=5):
    """Process multiple flights in parallel"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_flight, path)
            for path in igc_file_paths
        ]
        results = [future.result() for future in futures]
    return results

# Usage
flights = ['flight1.igc', 'flight2.igc', 'flight3.igc']
results = process_batch(flights, max_workers=5)
```

### Pattern 3: Incremental Processing with Checkpoints

Process large batches with checkpoints for recovery:

```python
import json
from pathlib import Path

def process_with_checkpoints(igc_files, checkpoint_file='progress.json'):
    """Process files with checkpoint support"""
    # Load checkpoint
    checkpoint = {}
    if Path(checkpoint_file).exists():
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
    
    processed = checkpoint.get('processed', [])
    results = checkpoint.get('results', {})
    
    # Process remaining files
    for igc_file in igc_files:
        if igc_file in processed:
            continue  # Skip already processed
        
        try:
            # Process file
            result = process_single_flight(igc_file)
            results[igc_file] = result
            processed.append(igc_file)
            
            # Save checkpoint
            checkpoint = {'processed': processed, 'results': results}
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f)
        
        except Exception as e:
            print(f"Error processing {igc_file}: {e}")
            # Continue with next file
    
    return results
```

### Pattern 4: Progressive Enhancement

Start with basic analysis and add details as needed:

```python
def progressive_analysis(igc_file_path, options):
    """
    Progressive flight analysis based on options
    Options can include: 'terrain', 'score', 'location'
    """
    results = {}
    
    # Always get basic metrics
    with open(igc_file_path, 'rb') as f:
        response = requests.post('http://xcmetrics:8081/', files={'file': f})
        response.raise_for_status()
        results['metrics'] = response.json()
    
    # Optional enhancements
    if 'terrain' in options:
        track_points = {"track_points": results['metrics']['track_points']}
        response = requests.post('http://dem:8084/', json=track_points)
        response.raise_for_status()
        results['terrain'] = response.json()
    
    if 'score' in options:
        with open(igc_file_path, 'rb') as f:
            response = requests.post('http://xcscore:8083/', files={'file': f})
            response.raise_for_status()
            results['score'] = response.json()
    
    if 'location' in options:
        first_point = results['metrics']['track_points'][0]
        response = requests.get(
            'http://geolookup:8082/nearest_town',
            params={'lat': first_point['lat'], 'lon': first_point['lon']}
        )
        response.raise_for_status()
        results['location'] = response.json()
    
    return results
```

## API Reference

### xcmetrics: POST /

Process an IGC file and return flight metrics.

**Request**:
```http
POST / HTTP/1.1
Host: localhost:8081
Content-Type: multipart/form-data

file: [IGC file binary data]
```

**Request Example (Python)**:
```python
with open('flight.igc', 'rb') as f:
    response = requests.post('http://localhost:8081/', files={'file': f})
```

**Response** (200 OK):
```json
{
  "info": {
    "date": "2024-08-15",
    "pilot": "John Doe",
    "glider": "Ozone Zeno",
    "duration_seconds": 14520,
    "distance_km": 87.3,
    "max_altitude_m": 3245
  },
  "glides": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [[9.5, 47.5], [9.6, 47.6]]
        },
        "properties": {
          "segment_id": 0,
          "duration_seconds": 180,
          "distance_km": 3.2,
          "avg_speed_kmh": 64.0
        }
      }
    ]
  },
  "thermals": {
    "type": "FeatureCollection",
    "features": [...]
  },
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
}
```

**Errors**:
- `400 Bad Request`: Invalid IGC file or file format not .igc
- `500 Internal Server Error`: Processing error

---

### dem: POST /

Add terrain elevation to track points.

**Request**:
```http
POST / HTTP/1.1
Host: localhost:8084
Content-Type: application/json

{
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
}
```

**Request Example (Python)**:
```python
track_points = {"track_points": data['track_points']}
response = requests.post('http://localhost:8084/', json=track_points)
```

**Response** (200 OK):
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
      "terrain_alt": 1028.3
    }
  ]
}
```

**Notes**:
- `terrain_alt` is added to each point
- Value is `null` if DEM data not available for coordinates
- All original fields are preserved

**Errors**:
- `400 Bad Request`: Invalid input format
- `500 Internal Server Error`: DEM processing error

---

### xcscore: POST /

Score a cross-country flight.

**Request**:
```http
POST / HTTP/1.1
Host: localhost:8083
Content-Type: multipart/form-data

file: [IGC file binary data]
```

**Request Example (Python)**:
```python
with open('flight.igc', 'rb') as f:
    response = requests.post('http://localhost:8083/', files={'file': f})
```

**Response** (200 OK):
```json
{
  "score": 87.3,
  "distance_km": 87.3,
  "score_type": "free_flight",
  "turnpoints": [
    {"lat": 47.5, "lon": 9.5, "time": "10:23:45"},
    {"lat": 47.6, "lon": 9.6, "time": "11:45:12"}
  ]
}
```

**Errors**:
- `400 Bad Request`: Invalid IGC file
- `500 Internal Server Error`: Scoring error

---

### geolookup: GET /takeoffdb

Find nearby paragliding takeoff locations.

**Request**:
```http
GET /takeoffdb?lat=47.5&lon=9.5&radius=1000 HTTP/1.1
Host: localhost:8082
```

**Request Example (Python)**:
```python
response = requests.get(
    'http://localhost:8082/takeoffdb',
    params={'lat': 47.5, 'lon': 9.5, 'radius': 1000}
)
```

**Parameters**:
- `lat` (required): Latitude in decimal degrees
- `lon` (required): Longitude in decimal degrees
- `radius` (optional): Search radius in meters (default: 1000)

**Response** (200 OK):
```json
[
  {
    "name": "Niedere",
    "lat": 47.498,
    "lon": 9.512,
    "distance_m": 234,
    "altitude_m": 1850
  }
]
```

---

### geolookup: GET /nearest_town

Find the nearest town or city.

**Request**:
```http
GET /nearest_town?lat=47.5&lon=9.5 HTTP/1.1
Host: localhost:8082
```

**Request Example (Python)**:
```python
response = requests.get(
    'http://localhost:8082/nearest_town',
    params={'lat': 47.5, 'lon': 9.5}
)
```

**Response** (200 OK):
```json
{
  "name": "Bregenz",
  "country": "Austria",
  "lat": 47.5,
  "lon": 9.75,
  "distance_km": 15.2
}
```

---

### geolookup: GET /admin1

Get administrative region (state/province) for coordinates.

**Request**:
```http
GET /admin1?lat=47.5&lon=9.5 HTTP/1.1
Host: localhost:8082
```

**Request Example (Python)**:
```python
response = requests.get(
    'http://localhost:8082/admin1',
    params={'lat': 47.5, 'lon': 9.5}
)
```

**Response** (200 OK):
```json
{
  "country": "Austria",
  "admin1": "Vorarlberg"
}
```

**Errors**:
- `400 Bad Request`: No match found (shouldn't occur for most locations)

## Error Handling

### HTTP Status Codes

All services follow standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (bad file format, missing parameters)
- `500 Internal Server Error`: Service error

### Retry Strategy

Recommended retry strategy for batch processing:

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504],  # Retry on these status codes
    allowed_methods=["GET", "POST"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# Use session for requests
response = session.post('http://xcmetrics:8081/', files={'file': f})
```

### Error Response Format

Error responses include details in the response body:

```json
{
  "detail": "File format not .igc"
}
```

### Handling Specific Errors

```python
def safe_process_flight(igc_file_path):
    """Process flight with comprehensive error handling"""
    try:
        with open(igc_file_path, 'rb') as f:
            response = requests.post(
                'http://xcmetrics:8081/',
                files={'file': f},
                timeout=120
            )
        
        if response.status_code == 400:
            # Client error - don't retry
            print(f"Invalid file: {response.json()['detail']}")
            return None
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print(f"Timeout processing {igc_file_path}")
        return None
    
    except requests.exceptions.ConnectionError:
        print(f"Connection error - service may be down")
        return None
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

## Performance Tips

### 1. Use Connection Pooling

Reuse HTTP connections to reduce overhead:

```python
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20,  # Number of connection pools
    pool_maxsize=40       # Max connections per pool
)
session.mount('http://', adapter)
```

### 2. Parallel Processing

Process multiple files concurrently:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(process_flight, igc_files))
```

**Recommended max_workers**:
- Light files (<100KB): 10-20 workers
- Medium files (100KB-1MB): 5-10 workers
- Large files (>1MB): 3-5 workers

### 3. Batch Size Optimization

Process files in batches to balance throughput and memory:

```python
def chunks(lst, n):
    """Yield successive n-sized chunks from lst"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Process in batches of 50
for batch in chunks(igc_files, 50):
    results = process_batch(batch)
    save_results(results)
```

### 4. Timeout Configuration

Set appropriate timeouts based on file size:

```python
def get_timeout(file_size_bytes):
    """Calculate timeout based on file size"""
    if file_size_bytes < 100_000:  # <100KB
        return 30
    elif file_size_bytes < 1_000_000:  # <1MB
        return 60
    else:
        return 120
```

### 5. Response Streaming

For large responses, use streaming:

```python
response = requests.post(
    'http://xcmetrics:8081/',
    files={'file': f},
    stream=True
)

# Process in chunks
for chunk in response.iter_content(chunk_size=8192):
    process_chunk(chunk)
```

### 6. Compression

Enable compression for large JSON payloads:

```python
import gzip
import json

headers = {
    'Content-Type': 'application/json',
    'Content-Encoding': 'gzip'
}

data = json.dumps(track_points).encode('utf-8')
compressed_data = gzip.compress(data)

response = requests.post(
    'http://dem:8084/',
    data=compressed_data,
    headers=headers
)
```

## Example Implementations

### Celery Task with Full Pipeline

```python
from celery import Celery, group, chain
import requests

app = Celery('flight_processor', broker='redis://localhost:6379/0')

# Configure session for connection pooling
session = requests.Session()

@app.task(bind=True, max_retries=3)
def extract_metrics(self, igc_file_path):
    """Extract flight metrics"""
    try:
        with open(igc_file_path, 'rb') as f:
            response = session.post(
                'http://xcmetrics:8081/',
                files={'file': f},
                timeout=120
            )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@app.task
def add_terrain(metrics_data):
    """Add terrain elevation"""
    track_points = {"track_points": metrics_data['track_points']}
    response = session.post('http://dem:8084/', json=track_points)
    response.raise_for_status()
    
    metrics_data['track_points'] = response.json()['track_points']
    return metrics_data

@app.task
def get_location(metrics_data):
    """Get takeoff location"""
    first_point = metrics_data['track_points'][0]
    response = session.get(
        'http://geolookup:8082/nearest_town',
        params={'lat': first_point['lat'], 'lon': first_point['lon']}
    )
    response.raise_for_status()
    
    metrics_data['location'] = response.json()
    return metrics_data

@app.task
def save_results(metrics_data):
    """Save to database"""
    # Save to your database
    print(f"Saving flight data: {metrics_data['info']['date']}")
    return metrics_data

# Create pipeline
def process_flight_pipeline(igc_file_path):
    """Chain tasks together"""
    pipeline = chain(
        extract_metrics.s(igc_file_path),
        add_terrain.s(),
        get_location.s(),
        save_results.s()
    )
    return pipeline.apply_async()

# Process multiple flights in parallel
def process_multiple_flights(igc_file_paths):
    """Process multiple flights in parallel"""
    job = group(process_flight_pipeline(path) for path in igc_file_paths)
    result = job.apply_async()
    return result
```

### Django Management Command

```python
from django.core.management.base import BaseCommand
from django.db import transaction
import requests
from myapp.models import Flight

class Command(BaseCommand):
    help = 'Process uploaded flights'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10)

    def handle(self, *args, **options):
        session = requests.Session()
        
        # Get unprocessed flights
        flights = Flight.objects.filter(processed=False)[:options['batch_size']]
        
        for flight in flights:
            try:
                # Process flight
                with open(flight.igc_file.path, 'rb') as f:
                    response = session.post(
                        'http://localhost:8081/',
                        files={'file': f},
                        timeout=120
                    )
                response.raise_for_status()
                data = response.json()
                
                # Update database
                with transaction.atomic():
                    flight.metrics = data
                    flight.processed = True
                    flight.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Processed flight {flight.id}')
                )
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing flight {flight.id}: {e}')
                )
```

## Summary

Key points for batch processing:

1. **Use connection pooling** for efficiency
2. **Implement retry logic** with exponential backoff
3. **Process in parallel** with appropriate worker count
4. **Handle errors gracefully** - don't stop the entire batch
5. **Monitor timeouts** - adjust based on file size
6. **Use checkpoints** for long-running batches
7. **Configure services** with adequate workers for your load

For Celery integration, the microservices are production-ready with:
- Multiple worker processes for parallel handling
- Reasonable timeouts (120s default)
- Health checks for monitoring
- Proper error responses for retry logic
