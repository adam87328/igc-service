#!/usr/bin/env python
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import sys
import os
import tempfile
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'submodules/igc_lib'))
from submodules.igc_lib import igc_lib

app = FastAPI()

# Define the main route to accept the .igc file
@app.post("/process")
async def convert_igc(file: UploadFile = File(...)):
    # Ensure the uploaded file is a .igc file
    if not file.filename.endswith(".igc"):
        raise HTTPException(
            status_code=400, 
            detail="File format not supported. Please upload a .igc file.")

    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Call your script that processes the .igc file
        json_data = track_analysis(temp_path)

        # Return the processed JSON
        return JSONResponse(content=json_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    finally:
        # Clean up the temporary file
        os.remove(temp_path)

def track_analysis(input_file):
    """igc_lib wrapper, combined output dict
    
    Args:
        path to igc file
    """

    # igc_lib custom settings
    # todo: make igc_lib settings accessible through FastAPI
    class igcLibCfg(igc_lib.FlightParsingConfig):
        min_time_for_bearing_change = 2.0
        min_time_for_thermal = 30

    # load via igc_lib
    flight = igc_lib.Flight.create_from_file(input_file,igcLibCfg)

    # if flight invalid, return igc_lib debug info
    if not flight.valid:
        return {
            "valid"     : False,
            "reason"    : flight.notes
            }
    
    # combine and output
    return {
        "valid"     : True,
        "info"      : json.loads(flight.flight_summary()),
        "glides"    : json.loads(flight.glides_to_gdf().to_json()),
        "thermals"  : json.loads(flight.thermals_to_gdf().to_json())
         }