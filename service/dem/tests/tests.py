import unittest
import requests
import json
from pathlib import Path

class TestDEMicroservice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # microservice URL
        cls.url = "http://localhost:8080/"

    def test_service_up(self):
        """Test microservice is running, and responds to dummy GET"""
        response = requests.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, '{"message":"dem"}')

    def test_coordinate_list_input(self):
        """Test with simple coordinate list input"""
        # Test coordinates (Chamonix, France area)
        test_data = {
            "coordinates": [
                {"lat": 45.9237, "lon": 6.8694},  # Chamonix
                {"lat": 45.8326, "lon": 6.8652},  # Nearby point
            ]
        }
        
        response = requests.post(
            self.url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check structure
        self.assertIn("coordinates", result)
        self.assertEqual(len(result["coordinates"]), 2)
        
        # Check each coordinate has elevation
        for coord in result["coordinates"]:
            self.assertIn("lat", coord)
            self.assertIn("lon", coord)
            self.assertIn("ground_elevation", coord)
            # Elevation should be a number or None
            self.assertTrue(
                coord["ground_elevation"] is None or 
                isinstance(coord["ground_elevation"], (int, float))
            )

    def test_geojson_input(self):
        """Test with GeoJSON FeatureCollection input"""
        # Sample GeoJSON with a simple LineString
        test_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [6.8694, 45.9237],  # [lon, lat] format
                            [6.8652, 45.8326],
                            [6.8700, 45.9000]
                        ]
                    },
                    "properties": {
                        "name": "Test Track"
                    }
                }
            ]
        }
        
        response = requests.post(
            self.url,
            json=test_geojson,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check structure
        self.assertEqual(result["type"], "FeatureCollection")
        self.assertIn("features", result)
        self.assertEqual(len(result["features"]), 1)
        
        # Check ground_elevation was added to properties
        feature = result["features"][0]
        self.assertIn("properties", feature)
        self.assertIn("ground_elevation", feature["properties"])
        
        # Should have 3 elevation values
        elevations = feature["properties"]["ground_elevation"]
        self.assertEqual(len(elevations), 3)

    def test_point_geometry(self):
        """Test with Point geometry"""
        test_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [6.8694, 45.9237]
                    },
                    "properties": {}
                }
            ]
        }
        
        response = requests.post(
            self.url,
            json=test_geojson,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check ground_elevation was added
        feature = result["features"][0]
        self.assertIn("ground_elevation", feature["properties"])
        # Should have 1 elevation value
        self.assertEqual(len(feature["properties"]["ground_elevation"]), 1)

    def test_invalid_input(self):
        """Test with invalid input"""
        response = requests.post(
            self.url,
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 400)

    def test_empty_coordinates(self):
        """Test with empty coordinate list"""
        test_data = {"coordinates": []}
        
        response = requests.post(
            self.url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["coordinates"], [])

if __name__ == '__main__':
    unittest.main()
