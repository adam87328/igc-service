#!/usr/bin/env python3
"""
Copernicus DEM data access using rasterio.

This module provides functionality to read elevation data from
Copernicus DSM tiles stored on the local filesystem.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
import rasterio
from rasterio.windows import from_bounds

logger = logging.getLogger(__name__)


class CopernicusDEM:
    """
    Access Copernicus DSM tiles for elevation data.
    
    This class manages access to Copernicus DEM tiles stored on the local
    filesystem. It automatically selects the appropriate tile based on
    coordinates and caches opened datasets for performance.
    """
    
    def __init__(self, tiles_dir: str):
        """
        Initialize the Copernicus DEM reader.
        
        Args:
            tiles_dir: Directory containing Copernicus DSM tiles
        """
        self.tiles_dir = Path(tiles_dir)
        self.tile_cache: Dict[str, rasterio.DatasetReader] = {}
        
        if not self.tiles_dir.exists():
            logger.warning(f"Tiles directory does not exist: {tiles_dir}")
    
    def _get_tile_path(self, lat: float, lon: float) -> Optional[Path]:
        """
        Determine the tile file path for a given coordinate.
        
        Copernicus tiles are named by their lower-left corner.
        Each tile covers 1°x1°.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
        
        Returns:
            Path to the tile file, or None if not found
        """
        # Get the tile indices (floor of the coordinates)
        lat_idx = int(lat) if lat >= 0 else int(lat) - 1
        lon_idx = int(lon) if lon >= 0 else int(lon) - 1
        
        # Construct tile name
        ns = "N" if lat_idx >= 0 else "S"
        lat_tag = f"{ns}{abs(lat_idx):02d}_00"
        
        ew = "E" if lon_idx >= 0 else "W"
        lon_tag = f"{ew}{abs(lon_idx):03d}_00"
        
        tile_name = f"Copernicus_DSM_COG_10_{lat_tag}_{lon_tag}_DEM.tif"
        tile_path = self.tiles_dir / tile_name
        
        if tile_path.exists():
            return tile_path
        else:
            logger.debug(f"Tile not found: {tile_path}")
            return None
    
    def _get_tile_dataset(self, tile_path: Path) -> Optional[rasterio.DatasetReader]:
        """
        Get or open a rasterio dataset for a tile.
        
        Uses caching to avoid reopening files repeatedly.
        
        Args:
            tile_path: Path to the tile file
        
        Returns:
            Rasterio dataset or None if unable to open
        """
        tile_key = str(tile_path)
        
        if tile_key not in self.tile_cache:
            try:
                dataset = rasterio.open(tile_path)
                self.tile_cache[tile_key] = dataset
                logger.debug(f"Opened tile: {tile_path.name}")
            except Exception as e:
                logger.error(f"Failed to open tile {tile_path}: {e}")
                return None
        
        return self.tile_cache.get(tile_key)
    
    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """
        Get elevation at a single point.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
        
        Returns:
            Elevation in meters, or None if unavailable
        """
        # Get the appropriate tile
        tile_path = self._get_tile_path(lat, lon)
        if not tile_path:
            logger.debug(f"No tile available for {lat}, {lon}")
            return None
        
        # Open the dataset
        dataset = self._get_tile_dataset(tile_path)
        if not dataset:
            return None
        
        try:
            # Sample the elevation at the point
            # rasterio uses (row, col) indexing
            row, col = dataset.index(lon, lat)
            
            # Read the pixel value
            # Check bounds to avoid reading outside the dataset
            if 0 <= row < dataset.height and 0 <= col < dataset.width:
                elevation = dataset.read(1, window=((row, row+1), (col, col+1)))[0, 0]
                
                # Handle nodata values
                if dataset.nodata is not None and elevation == dataset.nodata:
                    logger.debug(f"Nodata value at {lat}, {lon}")
                    return None
                
                return float(elevation)
            else:
                logger.debug(f"Coordinates {lat}, {lon} outside tile bounds")
                return None
                
        except Exception as e:
            logger.error(f"Error reading elevation at {lat}, {lon}: {e}")
            return None
    
    def get_elevations_batch(self, coords: list) -> list:
        """
        Get elevations for a batch of coordinates.
        
        Args:
            coords: List of (lon, lat) tuples
        
        Returns:
            List of elevation values (or None for unavailable)
        """
        elevations = []
        for lon, lat in coords:
            elevation = self.get_elevation(lat, lon)
            elevations.append(elevation)
        
        return elevations
    
    def close(self):
        """Close all cached datasets."""
        for dataset in self.tile_cache.values():
            try:
                dataset.close()
            except Exception as e:
                logger.error(f"Error closing dataset: {e}")
        
        self.tile_cache.clear()
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()
