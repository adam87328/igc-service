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

    def test_track_points_input(self):
        """Test with new track_points format"""
        # Test track points
        test_data = {
            "track_points": [
                {
                    "timestamp": "2024-08-15T10:23:45Z",
                    "lat": 45.9237,
                    "lon": 6.8694,
                    "gps_alt": 1523,
                    "pressure_alt": 1520,
                    "segment_type": "glide",
                    "segment_id": 0
                },
                {
                    "timestamp": "2024-08-15T10:23:50Z",
                    "lat": 45.8326,
                    "lon": 6.8652,
                    "gps_alt": 1530,
                    "pressure_alt": 1527,
                    "segment_type": "thermal",
                    "segment_id": 1
                }
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
        self.assertIn("track_points", result)
        self.assertEqual(len(result["track_points"]), 2)
        
        # Check each track point has terrain_alt and original fields
        for i, track_point in enumerate(result["track_points"]):
            self.assertIn("timestamp", track_point)
            self.assertIn("lat", track_point)
            self.assertIn("lon", track_point)
            self.assertIn("gps_alt", track_point)
            self.assertIn("pressure_alt", track_point)
            self.assertIn("segment_type", track_point)
            self.assertIn("segment_id", track_point)
            self.assertIn("terrain_alt", track_point)
            
            # terrain_alt should be a number or None
            self.assertTrue(
                track_point["terrain_alt"] is None or 
                isinstance(track_point["terrain_alt"], (int, float))
            )
            
            # Verify original values are preserved
            self.assertEqual(track_point["lat"], test_data["track_points"][i]["lat"])
            self.assertEqual(track_point["lon"], test_data["track_points"][i]["lon"])
            self.assertEqual(track_point["timestamp"], test_data["track_points"][i]["timestamp"])

    def test_minimal_track_points(self):
        """Test with minimal track_points (only required fields)"""
        test_data = {
            "track_points": [
                {
                    "timestamp": "2024-08-15T10:23:45Z",
                    "lat": 45.9237,
                    "lon": 6.8694
                }
            ]
        }
        
        response = requests.post(
            self.url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("track_points", result)
        self.assertEqual(len(result["track_points"]), 1)
        self.assertIn("terrain_alt", result["track_points"][0])

    def test_invalid_input(self):
        """Test with invalid input"""
        response = requests.post(
            self.url,
            json={"invalid": "data"},
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 422)  # Validation error

    def test_empty_track_points(self):
        """Test with empty track_points list"""
        test_data = {"track_points": []}
        
        response = requests.post(
            self.url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["track_points"], [])

if __name__ == '__main__':
    unittest.main()
