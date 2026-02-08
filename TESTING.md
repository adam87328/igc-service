# Testing Guide for Queue-Based Processing

This guide explains how to test the microservices for queue-based processing scenarios.

## Prerequisites

Before testing, ensure all services are running:

```bash
# Start all services
docker compose up -d

# Verify services are healthy
docker compose ps
```

## Manual Testing

### 1. Health Checks

Verify all services are responding:

```bash
curl http://localhost:8081/  # xcmetrics
curl http://localhost:8082/  # geolookup  
curl http://localhost:8083/  # xcscore
curl http://localhost:8084/  # dem
```

### 2. Single Request Testing

Test individual endpoints:

```bash
# Test xcmetrics
curl -X POST http://localhost:8081/ \
  -F "file=@test/testdata/short_niedere.igc"

# Test geolookup
curl "http://localhost:8082/nearest_town?lat=47.5&lon=9.5"

# Test DEM
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

## Automated Load Testing

### Batch Test Script

The `test/batch_test.py` script simulates concurrent requests:

```bash
# Test all services with 10 concurrent requests
python test/batch_test.py

# Test with higher concurrency
python test/batch_test.py --concurrency 20

# Test specific service
python test/batch_test.py --service xcmetrics --concurrency 15

# Use custom IGC files
python test/batch_test.py --files flight1.igc flight2.igc --concurrency 10
```

### Expected Results

For default configuration (4 workers per service):

| Service | Concurrent Requests | Expected Throughput | Avg Response Time |
|---------|-------------------|---------------------|------------------|
| xcmetrics | 10 | 5-10 req/s | 2-5s |
| geolookup | 10 | 40-80 req/s | 50-150ms |
| xcscore | 10 | 5-10 req/s | 1-3s |
| dem | 10 | 10-20 req/s | 1-3s |

## Integration Testing

Test the complete workflow:

```bash
# Run integration test
python test/test_integration.py
```

This tests:
1. Upload IGC file to xcmetrics
2. Process track points with DEM service
3. Verify terrain elevation is added

## Production Simulation

### Simulate Celery Worker Load

Use the batch test script to simulate multiple Celery workers:

```bash
# Simulate 5 Celery workers processing 50 flights
python test/batch_test.py --concurrency 50 --service xcmetrics
```

### Monitor Performance

Watch Docker container stats during load testing:

```bash
# In another terminal
docker stats xcmetrics geolookup xcscore dem
```

Look for:
- CPU usage (should stay below 80% on average)
- Memory usage (should be stable, not growing)
- Network I/O (should be reasonable for your workload)

## Troubleshooting

### High Error Rates

If you see high error rates:

1. Check service logs:
   ```bash
   docker compose logs -f xcmetrics
   ```

2. Reduce concurrency:
   ```bash
   python test/batch_test.py --concurrency 5
   ```

3. Increase timeout:
   ```bash
   docker compose down
   export TIMEOUT=180
   docker compose up -d
   ```

### Slow Response Times

If response times are too slow:

1. Increase worker count:
   ```bash
   docker compose down
   export WORKERS=8
   docker compose up -d
   ```

2. Check system resources:
   ```bash
   docker stats
   ```

3. Consider horizontal scaling:
   ```bash
   docker compose up -d --scale xcmetrics=3
   ```

### Connection Timeouts

If you see connection timeouts:

1. Check health of services:
   ```bash
   docker compose ps
   ```

2. Restart services:
   ```bash
   docker compose restart
   ```

3. Check network connectivity:
   ```bash
   docker compose logs
   ```

## Performance Tuning

### Optimize for Your Workload

1. **Light Traffic** (< 10 req/s):
   ```bash
   export WORKERS=2
   export WORKER_CONNECTIONS=500
   ```

2. **Medium Traffic** (10-50 req/s):
   ```bash
   export WORKERS=4
   export WORKER_CONNECTIONS=1000
   ```

3. **Heavy Traffic** (> 50 req/s):
   ```bash
   export WORKERS=8
   export WORKER_CONNECTIONS=2000
   ```

Then restart services:
```bash
docker compose down
docker compose up -d
```

## Validation Checklist

Before deploying to production, verify:

- [ ] All health checks pass
- [ ] Single request testing works for all endpoints
- [ ] Batch testing completes without errors
- [ ] Response times are acceptable for your SLA
- [ ] Services can handle expected concurrent load
- [ ] Memory usage is stable under load
- [ ] CPU usage doesn't exceed 80% on average
- [ ] Error rates are below 1%
- [ ] Integration test passes

## Next Steps

Once testing is complete:

1. Review [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
2. Review [API_GUIDE.md](API_GUIDE.md) for Celery integration patterns
3. Set up monitoring and alerting
4. Configure auto-scaling if using Kubernetes
5. Set up log aggregation

## Support

For issues or questions:
- Check service logs: `docker compose logs -f [service]`
- Review documentation in DEPLOYMENT.md and API_GUIDE.md
- Check GitHub issues for known problems
