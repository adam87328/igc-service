from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import json

app = FastAPI()

@app.get("/compmetrics")
async def alive():
    return {"message": "comp-metrics alive"}

@app.post("/compmetrics")
async def process(file: UploadFile = File(...)):
    # Ensure the uploaded file is a .igc file
    if not file.filename.lower().endswith(".igc"):
        raise HTTPException(
            status_code=400, # bad request 
            detail="File format not .igc")
    
    try:
        data = await file.read()
        # call subfunction
        json_data = track_analysis(data.decode('ascii'))
        # Return the processed JSON
        return JSONResponse(content=json_data)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500, # Internal Server Error
                detail=f"Internal Error: {str(e)}")

def track_analysis(data):
    """igc-xc-score wrapper
    
    https://github.com/mmomtchev/igc-xc-score
    """

    # todo: choose executable based on OS
    program = ["./igc-xc-score-macos", 
        "quiet=true", 
        "pipe=true", 
        "noflight=true",
        "scoring=XContest"]
    
    # Start the process
    process = subprocess.Popen(
        program, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Enable text mode (for string input/output instead of bytes)
    )

    # Send input data and get the output
    stdout, stderr = process.communicate(input=data)

    # Check if any error occurred
    if stderr:
        raise HTTPException(
            status_code=500, # Internal Server Error
            detail=f"Internal Error: igc-xc-score: {stderr}")
    else:
        return json.loads(stdout)