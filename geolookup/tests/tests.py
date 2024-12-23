import unittest
import requests
from pathlib import Path
import json

class TestMicroservice(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        p = Path(__file__).resolve()
        # .igc files for testing
        self.testdata_dir = p.parents[2] / 'testdata'
        # microservice URL
        self.url = "http://localhost:8080/"

    def test_testdata_dir_exists(self):
        self.assertTrue(self.testdata_dir.is_dir(), 
            f"missing testdata directory {self.testdata_dir}")
    
    def test_service_up(self):
        """Test microservice is running, and responds GET"""
        response = requests.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.text,'{"message":"geolookup"}')

    def test_route_takeoffdb(self):
        """Test takeoff DB with known coordinate"""
        lat=47.399682
        lon=9.942572
        url = self.url + f"/takeoffdb?lat={lat}&lon={lon}"

        response = requests.get(url)
        d = json.loads(response.text)

        self.assertEqual(response.status_code,200)
        self.assertEqual( d["name"], "Niedere - Andelsbuch")

    def test_route_geocode(self):
        """Test geocode with known coordinate"""
        lat=47.399682
        lon=9.942572
        url = self.url + f"/geocode?lat={lat}&lon={lon}"

        response = requests.get(url)
        d = json.loads(response.text)
        
        self.assertEqual(response.status_code,200)
        self.assertEqual( d["city"], "Bizau")

if __name__ == '__main__':
    unittest.main()