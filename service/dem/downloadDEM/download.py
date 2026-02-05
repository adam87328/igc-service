#!/usr/bin/env python3
"""
Download Copernicus DSM tiles for the Alps region.

This script downloads DEM tiles from the Copernicus 30m dataset
covering the Alps region. Tiles can be stored in a configurable
directory on the local filesystem.

Usage:
    python download.py [output_dir]
    
    output_dir: Path where tiles should be stored (default: ./dem_tiles)
"""

import subprocess
import os
import sys
import argparse


def get_tile_name(lat_idx, lon_idx):
    """
    Generate Copernicus DSM tile name from lat/lon indices.
    
    Args:
        lat_idx: Integer latitude (e.g., 47 for 47°N)
        lon_idx: Integer longitude (e.g., 9 for 9°E)
    
    Returns:
        Tuple of (tile_base_name, s3_key)
    """
    ns = "N" if lat_idx >= 0 else "S"
    lat_tag = f"{ns}{abs(lat_idx):02d}_00"
    
    ew = "E" if lon_idx >= 0 else "W"
    lon_tag = f"{ew}{abs(lon_idx):03d}_00"
    
    tile_base = f"Copernicus_DSM_COG_10_{lat_tag}_{lon_tag}_DEM"
    s3_key = f"{tile_base}/{tile_base}.tif"
    
    return tile_base, s3_key


def download_tile(lat_idx, lon_idx, output_dir):
    """
    Download a single Copernicus DSM tile.
    
    Args:
        lat_idx: Integer latitude
        lon_idx: Integer longitude
        output_dir: Directory to save the tile
    
    Returns:
        True if download successful, False otherwise
    """
    tile_base, s3_key = get_tile_name(lat_idx, lon_idx)
    output_path = os.path.join(output_dir, f"{tile_base}.tif")
    
    # Skip if already exists
    if os.path.exists(output_path):
        print(f"Tile already exists: {output_path}")
        return True
    
    print(f"Downloading tile {lat_idx}°N, {lon_idx}°E...")
    print(f"  S3 key: {s3_key}")
    print(f"  Output: {output_path}")
    
    cmd = [
        "aws", "s3", "cp",
        f"s3://copernicus-dem-30m/{s3_key}",
        output_path,
        "--no-sign-request"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  ✓ Download successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Download failed: {e}")
        return False


def download_alps_region(output_dir):
    """
    Download all tiles covering the Alps region.
    
    The Alps region approximately covers:
    - Latitude: 43°N to 48°N
    - Longitude: 5°E to 17°E
    
    Args:
        output_dir: Directory to save tiles
    
    Returns:
        Number of successfully downloaded tiles
    """
    # Alps bounding box
    lat_min, lat_max = 43, 48
    lon_min, lon_max = 5, 17
    
    print(f"Downloading Copernicus DSM tiles for the Alps region")
    print(f"  Latitude range: {lat_min}°N to {lat_max}°N")
    print(f"  Longitude range: {lon_min}°E to {lon_max}°E")
    print(f"  Output directory: {output_dir}")
    print()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Download all tiles in the bounding box
    total_tiles = 0
    successful = 0
    
    for lat in range(lat_min, lat_max + 1):
        for lon in range(lon_min, lon_max + 1):
            total_tiles += 1
            if download_tile(lat, lon, output_dir):
                successful += 1
            print()
    
    print(f"Download complete: {successful}/{total_tiles} tiles successful")
    return successful


def main():
    parser = argparse.ArgumentParser(
        description="Download Copernicus DSM tiles for the Alps region"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="./dem_tiles",
        help="Directory to store downloaded tiles (default: ./dem_tiles)"
    )
    parser.add_argument(
        "--tile",
        nargs=2,
        type=int,
        metavar=("LAT", "LON"),
        help="Download a single tile instead of the full Alps region (e.g., --tile 47 9)"
    )
    
    args = parser.parse_args()
    
    if args.tile:
        # Download single tile
        lat, lon = args.tile
        os.makedirs(args.output_dir, exist_ok=True)
        success = download_tile(lat, lon, args.output_dir)
        sys.exit(0 if success else 1)
    else:
        # Download entire Alps region
        successful = download_alps_region(args.output_dir)
        sys.exit(0 if successful > 0 else 1)


if __name__ == "__main__":
    main()