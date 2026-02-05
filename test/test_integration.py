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
    # File paths
    testdata_dir = Path(__file__).parent / "testdata"
    igc_file = testdata_dir / "valid_xctracer_mini_v.IGC"
    
    print("=" * 70)
    print("Integration Test: xcmetrics → DEM Service")
    print("=" * 70)
    
    # Step 1: Process IGC file with xcmetrics
    print("\n1. Processing IGC file with xcmetrics...")
    xcmetrics_url = "http://localhost:8081/"
    
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
    
    # Step 2: Send glides GeoJSON to DEM service
    print("\n2. Adding ground elevation to glides...")
    dem_url = "http://localhost:8084/"
    
    glides_geojson = xcmetrics_data.get('glides', {})
    if glides_geojson and glides_geojson.get('features'):
        response = requests.post(
            dem_url,
            json=glides_geojson,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ✗ DEM service failed: {response.status_code}")
            return
        
        enhanced_glides = response.json()
        print(f"   ✓ DEM service successful")
        
        # Show sample elevations
        for i, feature in enumerate(enhanced_glides['features'][:3]):  # Show first 3
            elevations = feature['properties'].get('ground_elevation', [])
            if elevations:
                print(f"   - Glide {i+1}: {len(elevations)} points, "
                      f"elevation range: {min(elevations):.1f}m - {max(elevations):.1f}m")
    else:
        print("   - No glides to process")
    
    # Step 3: Send thermals GeoJSON to DEM service
    print("\n3. Adding ground elevation to thermals...")
    thermals_geojson = xcmetrics_data.get('thermals', {})
    if thermals_geojson and thermals_geojson.get('features'):
        response = requests.post(
            dem_url,
            json=thermals_geojson,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"   ✗ DEM service failed: {response.status_code}")
            return
        
        enhanced_thermals = response.json()
        print(f"   ✓ DEM service successful")
        
        # Show sample elevations
        for i, feature in enumerate(enhanced_thermals['features'][:3]):  # Show first 3
            elevations = feature['properties'].get('ground_elevation', [])
            if elevations:
                print(f"   - Thermal {i+1}: {len(elevations)} points, "
                      f"elevation range: {min(elevations):.1f}m - {max(elevations):.1f}m")
    else:
        print("   - No thermals to process")
    
    # Step 4: Demonstrate coordinate list format
    print("\n4. Alternative: Using coordinate list format...")
    sample_coords = {
        "coordinates": [
            {"lat": 45.9237, "lon": 6.8694},  # Chamonix area
            {"lat": 45.8326, "lon": 6.8652},
        ]
    }
    
    response = requests.post(
        dem_url,
        json=sample_coords,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Coordinate list format successful")
        for coord in result['coordinates']:
            ground_elev = coord.get('ground_elevation')
            if ground_elev is not None:
                print(f"   - {coord['lat']:.4f}, {coord['lon']:.4f}: "
                      f"{ground_elev:.1f}m elevation")
            else:
                print(f"   - {coord['lat']:.4f}, {coord['lon']:.4f}: no elevation data")
    else:
        print(f"   ✗ Failed: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("Integration test complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
