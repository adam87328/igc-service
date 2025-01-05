from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# offline DB of towns/cities, returns closest match
from nearest_town import NearestTown
# offline DB of paraglinding takeoff locations, paraglidingearth.com
from named_takeoff import NamedTakeoff
# offline DB of admin-1 (state/province) borders
# https://www.naturalearthdata.com/downloads/10m-cultural-vectors
from country_state import CountryState

app = FastAPI()
takeoff = NamedTakeoff()
state = CountryState()
town = NearestTown()

@app.get("/")
async def alive():
    return {"message": "geolookup"}

@app.get("/takeoffdb")
async def takeoffdb(lat: float, lon: float, radius: float = 1000):
    return JSONResponse( content = takeoff.query(lat,lon,radius) )

@app.get("/nearest_town")
async def takeoffdb(lat: float, lon: float):
    ddict = town.query(lat, lon)
    return JSONResponse(ddict)

@app.get("/admin1")
async def takeoffdb(lat: float, lon: float):
    ddict = state.query(lat, lon)
    if ddict:
        return JSONResponse(ddict)
    else:
        # shouldn't occur
        raise HTTPException(
            status_code=400, # bad request
            detail=f"admin1: no match") 