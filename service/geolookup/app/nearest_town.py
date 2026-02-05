import reverse_geocode

class NearestTown:

    def query(self,lat,lon):
        ddict = reverse_geocode.get([lat, lon])
        # {
        #     "country_code": "AT",
        #     "city": "Bizau",
        #     "latitude": 47.36906,
        #     "longitude": 9.92839,
        #     "population": 1107,
        #     "state": "Vorarlberg",
        #     "county": "Politischer Bezirk Bregenz",
        #     "country": "Austria"
        # }
        return {
            "city"       : ddict['city'],
            "iso_3166_2" : ddict['country_code'],
            "db_lat"     : ddict['latitude'],
            "db_lon"     : ddict['longitude'],
        }


if __name__ == "__main__":
    """test"""
    obj = NearestTown()
    # Bezau, Niedere
    lat=47.399682
    lon=9.942572
    out = obj.query(lat,lon)
    print(out)