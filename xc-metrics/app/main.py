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

@app.get("/xcmetrics")
async def alive():
    return {"message": "xc-metrics alive"}

@app.post("/xcmetrics")
async def process(file: UploadFile = File(...)):
    # Ensure the uploaded file is a .igc file
    if not file.filename.lower().endswith(".igc"):
        raise HTTPException(
            status_code=400, # bad request 
            detail="File format not .igc")
    
    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as temp_file:
            temp_file.write(await file.read())
        # call subfunction
        json_data = track_analysis(temp_path)
        # Return the processed JSON
        return JSONResponse(content=json_data)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500, # Internal Server Error
                detail=f"Internal Error: {str(e)}")
    
    finally:
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
        raise HTTPException(
            status_code=400, # bad request
            detail=f"igc_lib: flight invalid: %s" % flight.notes)

    # combine and output
    g_json = flight.glides_to_gdf().to_json() if flight.glides else "{}"
    t_json = flight.thermals_to_gdf().to_json() if flight.thermals else "{}"

    return {
        "info"      : json.loads(flight.flight_summary()),
        "glides"    : json.loads(g_json),
        "thermals"  : json.loads(t_json),
         }