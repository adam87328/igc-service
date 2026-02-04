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

Use the tmux script to start all services:
```bash
./run_tmux.sh
```

Then attach to the session:
```bash
tmux attach -t igcservice
```

## Integration Example

See `test_integration.py` for a complete example of using xcmetrics and DEM services together:

```python
# 1. Process IGC file with xcmetrics
response = requests.post('http://localhost:8081/', files={'file': igc_file})
xcmetrics_data = response.json()

# 2. Add ground elevation data with DEM service
response = requests.post('http://localhost:8084/', json=xcmetrics_data['glides'])
enhanced_data = response.json()
```