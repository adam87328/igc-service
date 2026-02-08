#!/usr/bin/env python3
"""
Batch testing script for validating concurrent/queued request handling.

This script simulates multiple concurrent requests to test the microservices
under load, similar to what would happen with Celery task queues.

Usage:
    # Test with default settings (10 concurrent requests)
    python batch_test.py
    
    # Test with custom concurrency
    python batch_test.py --concurrency 20
    
    # Test specific service
    python batch_test.py --service xcmetrics
    
    # Test with multiple IGC files
    python batch_test.py --files test/testdata/*.igc
"""

import argparse
import requests
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import statistics


class ServiceTester:
    """Test microservices with concurrent requests"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=50,
            pool_maxsize=100,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def test_xcmetrics(self, igc_file_path: str) -> Dict[str, Any]:
        """Test xcmetrics service"""
        start_time = time.time()
        
        try:
            with open(igc_file_path, 'rb') as f:
                response = self.session.post(
                    f'{self.base_url}:8081/',
                    files={'file': f},
                    timeout=120
                )
            
            elapsed = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'elapsed': elapsed,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else response.text
            }
        
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'elapsed': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }
    
    def test_dem(self, track_points: List[Dict]) -> Dict[str, Any]:
        """Test DEM service"""
        start_time = time.time()
        
        try:
            payload = {"track_points": track_points}
            response = self.session.post(
                f'{self.base_url}:8084/',
                json=payload,
                timeout=90
            )
            
            elapsed = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'elapsed': elapsed,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else response.text
            }
        
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'elapsed': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }
    
    def test_xcscore(self, igc_file_path: str) -> Dict[str, Any]:
        """Test xcscore service"""
        start_time = time.time()
        
        try:
            with open(igc_file_path, 'rb') as f:
                response = self.session.post(
                    f'{self.base_url}:8083/',
                    files={'file': f},
                    timeout=120
                )
            
            elapsed = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'elapsed': elapsed,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else response.text
            }
        
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'elapsed': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }
    
    def test_geolookup_town(self, lat: float, lon: float) -> Dict[str, Any]:
        """Test geolookup nearest_town endpoint"""
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.base_url}:8082/nearest_town',
                params={'lat': lat, 'lon': lon},
                timeout=30
            )
            
            elapsed = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'elapsed': elapsed,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else response.text
            }
        
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'elapsed': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }
    
    def test_geolookup_takeoff(self, lat: float, lon: float, radius: int = 1000) -> Dict[str, Any]:
        """Test geolookup takeoffdb endpoint"""
        start_time = time.time()
        
        try:
            response = self.session.get(
                f'{self.base_url}:8082/takeoffdb',
                params={'lat': lat, 'lon': lon, 'radius': radius},
                timeout=30
            )
            
            elapsed = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'elapsed': elapsed,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else response.text
            }
        
        except Exception as e:
            return {
                'success': False,
                'status_code': None,
                'elapsed': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }


def print_statistics(results: List[Dict[str, Any]], service_name: str):
    """Print statistics from test results"""
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # Calculate timing statistics
    elapsed_times = [r['elapsed'] for r in results if r['success']]
    
    if elapsed_times:
        avg_time = statistics.mean(elapsed_times)
        min_time = min(elapsed_times)
        max_time = max(elapsed_times)
        median_time = statistics.median(elapsed_times)
        
        if len(elapsed_times) > 1:
            stdev_time = statistics.stdev(elapsed_times)
        else:
            stdev_time = 0
    else:
        avg_time = min_time = max_time = median_time = stdev_time = 0
    
    # Print results
    print(f"\n{'='*70}")
    print(f"  {service_name} Test Results")
    print(f"{'='*70}")
    print(f"  Total Requests:     {total}")
    print(f"  Successful:         {successful} ({success_rate:.1f}%)")
    print(f"  Failed:             {failed}")
    print(f"\n  Response Time Statistics:")
    print(f"  - Average:          {avg_time:.3f}s")
    print(f"  - Median:           {median_time:.3f}s")
    print(f"  - Min:              {min_time:.3f}s")
    print(f"  - Max:              {max_time:.3f}s")
    print(f"  - Std Dev:          {stdev_time:.3f}s")
    
    if failed > 0:
        print(f"\n  Errors:")
        for i, result in enumerate(results):
            if not result['success']:
                print(f"  - Request {i+1}: {result['error']}")
    
    print(f"{'='*70}")


def test_xcmetrics_concurrent(tester: ServiceTester, igc_files: List[str], 
                               concurrency: int) -> List[Dict[str, Any]]:
    """Test xcmetrics with concurrent requests"""
    
    print(f"\nTesting xcmetrics with {concurrency} concurrent requests...")
    print(f"Using {len(igc_files)} IGC file(s)")
    
    # Create work items (repeat files if needed)
    work_items = []
    while len(work_items) < concurrency:
        work_items.extend(igc_files)
    work_items = work_items[:concurrency]
    
    # Execute concurrently
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(tester.test_xcmetrics, file): file 
                   for file in work_items}
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            # Progress indicator
            if i % 10 == 0 or i == len(futures):
                print(f"  Progress: {i}/{len(futures)} requests completed")
    
    total_time = time.time() - start_time
    requests_per_sec = concurrency / total_time if total_time > 0 else 0
    
    print(f"\n  Total Time: {total_time:.2f}s")
    print(f"  Throughput: {requests_per_sec:.2f} requests/second")
    
    return results


def test_dem_concurrent(tester: ServiceTester, concurrency: int) -> List[Dict[str, Any]]:
    """Test DEM with concurrent requests"""
    
    print(f"\nTesting DEM with {concurrency} concurrent requests...")
    
    # Sample track points
    sample_track_points = [
        {
            "timestamp": "2024-08-15T10:23:45Z",
            "lat": 47.5 + i * 0.01,
            "lon": 9.5 + i * 0.01,
            "gps_alt": 1500 + i * 10,
            "pressure_alt": 1500 + i * 10,
            "segment_type": "glide",
            "segment_id": 0
        }
        for i in range(10)
    ]
    
    # Execute concurrently
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(tester.test_dem, sample_track_points) 
                   for _ in range(concurrency)]
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            if i % 10 == 0 or i == len(futures):
                print(f"  Progress: {i}/{len(futures)} requests completed")
    
    total_time = time.time() - start_time
    requests_per_sec = concurrency / total_time if total_time > 0 else 0
    
    print(f"\n  Total Time: {total_time:.2f}s")
    print(f"  Throughput: {requests_per_sec:.2f} requests/second")
    
    return results


def test_geolookup_concurrent(tester: ServiceTester, concurrency: int) -> List[Dict[str, Any]]:
    """Test geolookup with concurrent requests"""
    
    print(f"\nTesting geolookup with {concurrency} concurrent requests...")
    
    # Sample coordinates (Alps region)
    coordinates = [
        (47.5 + i * 0.1, 9.5 + i * 0.1)
        for i in range(20)
    ]
    
    # Execute concurrently
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Mix of different endpoint types
        futures = []
        for i in range(concurrency):
            coord = coordinates[i % len(coordinates)]
            if i % 2 == 0:
                future = executor.submit(tester.test_geolookup_town, coord[0], coord[1])
            else:
                future = executor.submit(tester.test_geolookup_takeoff, coord[0], coord[1])
            futures.append(future)
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            results.append(result)
            
            if i % 10 == 0 or i == len(futures):
                print(f"  Progress: {i}/{len(futures)} requests completed")
    
    total_time = time.time() - start_time
    requests_per_sec = concurrency / total_time if total_time > 0 else 0
    
    print(f"\n  Total Time: {total_time:.2f}s")
    print(f"  Throughput: {requests_per_sec:.2f} requests/second")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Batch test microservices with concurrent requests'
    )
    parser.add_argument(
        '--concurrency', 
        type=int, 
        default=10,
        help='Number of concurrent requests (default: 10)'
    )
    parser.add_argument(
        '--service',
        choices=['all', 'xcmetrics', 'dem', 'geolookup', 'xcscore'],
        default='all',
        help='Service to test (default: all)'
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost',
        help='Base URL for services (default: http://localhost)'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='IGC files to use for testing (default: test/testdata/*.igc)'
    )
    
    args = parser.parse_args()
    
    # Find IGC files
    if args.files:
        igc_files = args.files
    else:
        # Look for test files
        test_dir = Path(__file__).parent / 'test' / 'testdata'
        if test_dir.exists():
            igc_files = list(test_dir.glob('*.igc'))
        else:
            igc_files = []
    
    if not igc_files and args.service in ['all', 'xcmetrics', 'xcscore']:
        print("Error: No IGC files found for testing.")
        print("Please provide IGC files with --files option")
        return 1
    
    igc_files = [str(f) for f in igc_files]
    
    print("="*70)
    print("  Microservices Batch Testing")
    print("="*70)
    print(f"  Base URL: {args.base_url}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Service(s): {args.service}")
    if igc_files:
        print(f"  IGC Files: {len(igc_files)}")
    print("="*70)
    
    tester = ServiceTester(args.base_url)
    
    # Run tests
    try:
        if args.service in ['all', 'xcmetrics']:
            results = test_xcmetrics_concurrent(tester, igc_files, args.concurrency)
            print_statistics(results, "xcmetrics")
        
        if args.service in ['all', 'dem']:
            results = test_dem_concurrent(tester, args.concurrency)
            print_statistics(results, "DEM")
        
        if args.service in ['all', 'geolookup']:
            results = test_geolookup_concurrent(tester, args.concurrency)
            print_statistics(results, "geolookup")
        
        if args.service in ['all', 'xcscore']:
            results = test_xcmetrics_concurrent(tester, igc_files, args.concurrency)
            print_statistics(results, "xcscore")
        
        print("\n✓ Batch testing completed successfully!\n")
        return 0
    
    except KeyboardInterrupt:
        print("\n\n✗ Testing interrupted by user\n")
        return 1
    
    except Exception as e:
        print(f"\n\n✗ Error during testing: {e}\n")
        return 1


if __name__ == '__main__':
    exit(main())
