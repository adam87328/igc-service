import unittest
import requests
from pathlib import Path

class TestMicroservice(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        p = Path(__file__).resolve()
        # .igc files for testing
        self.testdata_dir = p.parent / 'resources'
        # microservice URL
        self.url = "http://localhost:8080/"

    def test_testdata_dir_exists(self):
        self.assertTrue(self.testdata_dir.is_dir(), 
            f"missing testdata directory {self.testdata_dir}")
    
    def test_service_up(self):
        """Test microservice is running, and responds to dummy GET"""
        response = requests.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.text,'{"message":"xcmetrics"}')

    def test_valid_files(self):
        """Test some valid igc files"""
        with open(self.testdata_dir / 'valid_xctracer_mini_v.IGC','rb') as f:
            file = {'file': f, }
            response = requests.post(self.url, files=file)
            self.assertEqual(response.status_code,200)
        with open(self.testdata_dir / 'valid_xctrack.IGC','rb') as f:
            file = {'file': f, }
            response = requests.post(self.url, files=file)
            self.assertEqual(response.status_code,200)

    def test_invalid(self):
        """Invalid igc file
        
        In this case, igc_lib reports invalid, which is turned into 
        a HTTPException by the microservice.
        """
        with open(self.testdata_dir / 'invalid_empty.igc','rb') as f:
            file = {'file': f, }
            response = requests.post(self.url, files=file)
            self.assertEqual(response.status_code,400)
            # response.text
            # {"detail":"igc_lib: flight invalid: ['Error: This file has 0 fixes, less than the minimum 50.']"}

    def test_internal_exception(self):
        """todo, trigger an exception in igc_lib"""
        pass 
        # self.assertEqual(response.status_code,400)
                
if __name__ == '__main__':
    unittest.main()