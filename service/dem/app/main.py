#!/usr/bin/env python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager
from copernicus_dem import CopernicusDEM
from config import DEM_TILES_DIR

logger = logging.getLogger(__name__)

# Global DEM reader instance
dem_reader = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage DEM reader lifecycle."""
    global dem_reader
    
    # Startup: Initialize DEM reader
    try:
        dem_reader = CopernicusDEM(DEM_TILES_DIR)
        logger.info(f"Copernicus DEM initialized with tiles from: {DEM_TILES_DIR}")
    except Exception as e:
        logger.error(f"Failed to initialize Copernicus DEM: {e}")
        dem_reader = None
    
    yield
    
    # Shutdown: Close DEM reader
    if dem_reader:
        try:
            dem_reader.close()
            logger.info("Copernicus DEM closed")
        except Exception as e:
            logger.error(f"Error closing DEM reader: {e}")

app = FastAPI(lifespan=lifespan)

class TrackPoint(BaseModel):
    """Single track point with optional altitude and segment information"""
    timestamp: str  # ISO 8601 format
    lat: float
    lon: float
    gps_alt: Optional[float] = None  # meters
    pressure_alt: Optional[float] = None  # meters
    segment_type: Optional[str] = None  # "glide" or "thermal"
    segment_id: Optional[int] = None

class TrackPointsInput(BaseModel):
    """Enhanced timeseries format"""
    track_points: List[TrackPoint]

@app.get("/")
async def alive():
    return {"message": "dem"}

@app.post("/")
async def process(input_data: TrackPointsInput):
    """
    Add digital elevation model (terrain elevation) data to track points.
    
    Accepts:
    - Enhanced timeseries format with track_points
    
    Returns:
    - Track points with terrain_alt added to each point
    """
    try:
        return await process_track_points(input_data.track_points)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            logger.error(f"Error processing request: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal Error: {str(e)}"
            )

async def process_track_points(track_points: List[TrackPoint]) -> Dict[str, Any]:
    """
    Process a list of track points and add terrain elevation to each.
    
    Args:
        track_points: List of TrackPoint objects
        
    Returns:
        Dict with track_points enhanced with terrain_alt field
    """
    # Convert to [lon, lat] format for API
    coords = [[tp.lon, tp.lat] for tp in track_points]
    
    # Get elevations
    elevations = await get_elevations_batch(coords)
    
    # Return enhanced data
    result = []
    for track_point, terrain_alt in zip(track_points, elevations):
        point_dict = track_point.model_dump()
        point_dict["terrain_alt"] = terrain_alt
        result.append(point_dict)
    
    return {"track_points": result}

async def get_elevations_batch(coords: List[List[float]]) -> List[Optional[float]]:
    """
    Get elevations for a batch of coordinates using Copernicus DEM data.
    
    Args:
        coords: List of [lon, lat] pairs
        
    Returns:
        List of elevation values in meters (or None if unavailable)
    """
    if not coords:
        return []
    
    elevations = []
    for coord in coords:
        try:
            # coords are in [lon, lat] format
            lat, lon = coord[1], coord[0]
            
            if dem_reader:
                # Use Copernicus DEM data
                elevation = dem_reader.get_elevation(lat, lon)
            else:
                # Fallback to None if DEM reader not available
                logger.warning("DEM reader not available, returning None")
                elevation = None
            
            logger.debug(f"Elevation for {lat}, {lon}: {elevation}")
            elevations.append(elevation)
        except Exception as e:
            logger.error(f"Error fetching elevation for {lat}, {lon}", exc_info=True)
            elevations.append(None)
    
    return elevations
