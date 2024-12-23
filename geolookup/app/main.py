from fastapi import FastAPI
from fastapi.responses import JSONResponse
import reverse_geocode

from named_takeoff import NamedTakeoff

app = FastAPI()
nt = NamedTakeoff()

@app.get("/takeoffdb")
async def takeoffdb(lat: float, lon: float, radius: float = 1000):
    """ example, default search radius 1 km
    /geocode?lat=47.399682&lon=9.942572
    {
        "name": "Niedere - Andelsbuch",
        "country": "AT",
        "dist": 747.4395282905823,
        "db_lat": 47.40349999999999,
        "db_lon": 9.93893
    }
    """
    return JSONResponse( content = nt.query(lat,lon,radius) )

@app.get("/geocode")
async def takeoffdb(lat: float, lon: float):
    """ example
    /geocode?lat=47.399682&lon=9.942572
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
    return JSONResponse( content = reverse_geocode.get([lat, lon]) )