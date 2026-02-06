#!/usr/bin/env python3
"""
Example integration test showing xcmetrics + DEM workflow

This demonstrates:
1. Processing an IGC file with xcmetrics to get glides/thermals GeoJSON
2. Sending that GeoJSON to DEM service to add ground elevation data
"""

import requests
import json
from pathlib import Path

def main():
    xcmetrics_url = "http://localhost:8081/"
    dem_url = "http://localhost:8084/"
    
    # File paths
    testdata_dir = Path(__file__).parent / "testdata"
    igc_file = testdata_dir / "valid_xctrack.igc"
    
    print("=" * 70)
    print("Integration Test: xcmetrics → DEM Service")
    print("=" * 70)
    
    # Step 1: Process IGC file with xcmetrics
    print("\n1. Processing IGC file with xcmetrics...")
    with open(igc_file, 'rb') as f:
        files = {'file': f}
        response = requests.post(xcmetrics_url, files=files)
    
    if response.status_code != 200:
        print(f"   ✗ xcmetrics failed: {response.status_code}")
        return
    
    xcmetrics_data = response.json()
    print(f"   ✓ xcmetrics successful")
    print(f"   - Glides: {len(xcmetrics_data.get('glides', {}).get('features', []))} features")
    print(f"   - Thermals: {len(xcmetrics_data.get('thermals', {}).get('features', []))} features")
    print(f"   - Track points: {len(xcmetrics_data.get('track_points', {}))} points")
    
    # Step 2: Send track points to DEM service
    print("\n2. Adding ground elevation to track points...")
    track_points_payload = {"track_points": xcmetrics_data.get('track_points') or []}
    
    output_path = Path(__file__).parent / "track_points.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(track_points_payload, f, indent=2)
    
    response = requests.post(
        dem_url,
        json=track_points_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"   ✗ DEM service failed: {response.status_code}")
        return
    
    track_points_out = response.json()
    print(f"   ✓ DEM service successful")
    
    # Show sample elevations
    for i, point in enumerate(track_points_out.get("track_points")[:3]):  # Show first 3
        terrain_alt = point.get('terrain_alt', [])
        if terrain_alt:
            print(f"   - terrain alt {i+1}: {(terrain_alt):.1f}m")
    
    output_path = Path(__file__).parent / "track_points_with_terrain_alt.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(track_points_out, f, indent=2)
    
    print("\n" + "=" * 70)
    print("Integration test complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
