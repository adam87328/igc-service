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
        self.assertEqual(response.status_code,200)

        d = json.loads(response.text)
        self.assertEqual( d["name"], "Niedere - Andelsbuch")

    def test_route_nearest_town(self):
        """Test nearest_town with known coordinate"""
        lat=47.399682
        lon=9.942572
        url = self.url + f"/nearest_town?lat={lat}&lon={lon}"

        response = requests.get(url)
        self.assertEqual(response.status_code,200)

        d = json.loads(response.text)
        self.assertEqual( d["city"], "Bizau")
        self.assertEqual( d["iso_3166_2"], "AT")

    def test_route_admin1(self):
        """Test nearest_town with known coordinate"""
        lat=47.399682
        lon=9.942572
        url = self.url + f"/admin1?lat={lat}&lon={lon}"

        response = requests.get(url)
        self.assertEqual(response.status_code,200)

        d = json.loads(response.text)
        self.assertEqual( d["admin0"], "Austria")
        self.assertEqual( d["admin1"], "Vorarlberg")
        self.assertEqual( d["iso_3166_1"], "AT-8")
        self.assertEqual( d["iso_3166_2"], "AT")


if __name__ == '__main__':
    unittest.main()