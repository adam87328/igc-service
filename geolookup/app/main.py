from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# offline DB of towns/cities, returns closest match
import reverse_geocode
# offline DB of paraglinding takeoff locations, paraglidingearth.com
from named_takeoff import NamedTakeoff
# offline DB of admin-1 (state/province) borders
# https://www.naturalearthdata.com/downloads/10m-cultural-vectors
from country_state import CountryState

app = FastAPI()
nt = NamedTakeoff()
cs = CountryState()

@app.get("/")
async def alive():
    return {"message": "geolookup"}

@app.get("/takeoffdb")
async def takeoffdb(lat: float, lon: float, radius: float = 1000):
    return JSONResponse( content = nt.query(lat,lon,radius) )

@app.get("/nearest_town")
async def takeoffdb(lat: float, lon: float):
    """ example
    /nearest_town?lat=47.399682&lon=9.942572
    {
        "country_code": "AT",
        "city": "Bizau",
        "latitude": 47.36906,
        "longitude": 9.92839,
        "population": 1107,
        "state": "Vorarlberg",
        "county": "Politischer Bezirk Bregenz",
        "country": "Austria"
    }
    """
    return JSONResponse( content = reverse_geocode.get([lat, lon]))

@app.get("/admin1")
async def takeoffdb(lat: float, lon: float):
    ddict = cs.query(lat, lon)
    if ddict:
        return JSONResponse(ddict)
    else:
        # shouldn't occur
        raise HTTPException(
            status_code=400, # bad request
            detail=f"admin1: no match") 