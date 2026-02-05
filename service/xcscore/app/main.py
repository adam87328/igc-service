from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from igc_xc_score_wrapper import igc_xc_score

app = FastAPI()

@app.get("/")
async def alive():
    return {"message": "xcscore"}

@app.post("/")
async def process(file: UploadFile = File(...)):
    # Ensure the uploaded file is a .igc file
    if not file.filename.lower().endswith(".igc"):
        raise HTTPException(
            status_code=400, # bad request 
            detail="File format not .igc")
    
    try:
        data = await file.read()
        # call subfunction
        json_data = igc_xc_score(data.decode('ascii'))
        # Return the processed JSON
        return JSONResponse(content=json_data)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500, # Internal Server Error
                detail=f"Internal Error: {str(e)}")
