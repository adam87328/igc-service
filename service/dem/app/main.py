#!/usr/bin/env python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import logging
from copernicus_dem import CopernicusDEM
from config import DEM_TILES_DIR

app = FastAPI()
logger = logging.getLogger(__name__)

# Initialize Copernicus DEM reader
try:
    dem_reader = CopernicusDEM(DEM_TILES_DIR)
    logger.info(f"Copernicus DEM initialized with tiles from: {DEM_TILES_DIR}")
except Exception as e:
    logger.error(f"Failed to initialize Copernicus DEM: {e}")
    dem_reader = None

class Coordinate(BaseModel):
    """Single coordinate point"""
    lat: float
    lon: float

class CoordinateList(BaseModel):
    """List of coordinates"""
    coordinates: List[Coordinate]

class GeoJSONInput(BaseModel):
    """Flexible input that accepts either GeoJSON or coordinate list"""
    geojson: Optional[Dict[str, Any]] = None
    coordinates: Optional[List[Coordinate]] = None

@app.get("/")
async def alive():
    return {"message": "dem"}

@app.post("/")
async def process(input_data: Union[Dict[str, Any], GeoJSONInput]):
    """
    Add digital elevation model (ground elevation) data to coordinates.
    
    Accepts:
    - GeoJSON FeatureCollection (from xcmetrics)
    - Simple coordinate list [{lat, lon}, ...]
    - Mixed input with both
    
    Returns:
    - Enhanced GeoJSON with ground_elevation added to properties
    - Or coordinate list with elevation data
    """
    try:
        # Handle different input types
        if isinstance(input_data, dict):
            # Direct dict input - check if it's GeoJSON or coordinate list
            if "type" in input_data and input_data["type"] == "FeatureCollection":
                # GeoJSON input
                return await process_geojson(input_data)
            elif "coordinates" in input_data:
                # Coordinate list input
                coords = [Coordinate(**c) for c in input_data["coordinates"]]
                return await process_coordinates(coords)
            elif "geojson" in input_data:
                # Wrapped GeoJSON
                return await process_geojson(input_data["geojson"])
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input format. Expected GeoJSON FeatureCollection or coordinate list"
                )
        else:
            # Pydantic model input
            if input_data.geojson:
                return await process_geojson(input_data.geojson)
            elif input_data.coordinates:
                return await process_coordinates(input_data.coordinates)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either geojson or coordinates must be provided"
                )
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            logger.error(f"Error processing request: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal Error: {str(e)}"
            )

async def process_geojson(geojson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process GeoJSON FeatureCollection and add ground elevation to each feature.
    
    Args:
        geojson_data: GeoJSON FeatureCollection with LineString geometries
        
    Returns:
        Enhanced GeoJSON with ground_elevation array added to properties
    """
    if geojson_data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=400,
            detail="GeoJSON must be a FeatureCollection"
        )
    
    features = geojson_data.get("features", [])
    
    for feature in features:
        geometry = feature.get("geometry", {})
        if geometry.get("type") in ["LineString", "MultiLineString", "Point"]:
            # Extract coordinates
            coords = []
            if geometry["type"] == "LineString":
                coords = geometry["coordinates"]
            elif geometry["type"] == "Point":
                coords = [geometry["coordinates"]]
            elif geometry["type"] == "MultiLineString":
                # Flatten MultiLineString
                for line in geometry["coordinates"]:
                    coords.extend(line)
            
            # Get elevations for all points
            elevations = await get_elevations_batch(coords)
            
            # Add to properties
            if "properties" not in feature:
                feature["properties"] = {}
            feature["properties"]["ground_elevation"] = elevations
    
    return geojson_data

async def process_coordinates(coordinates: List[Coordinate]) -> Dict[str, Any]:
    """
    Process a list of coordinates and return them with elevation data.
    
    Args:
        coordinates: List of Coordinate objects
        
    Returns:
        Dict with coordinates and their elevations
    """
    # Convert to [lon, lat] format for API
    coords = [[c.lon, c.lat] for c in coordinates]
    
    # Get elevations
    elevations = await get_elevations_batch(coords)
    
    # Return enhanced data
    result = []
    for coord, elev in zip(coordinates, elevations):
        result.append({
            "lat": coord.lat,
            "lon": coord.lon,
            "ground_elevation": elev
        })
    
    return {"coordinates": result}

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
