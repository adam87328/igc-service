import os
import geopandas as gpd
from shapely.geometry import Point

class CountryState:
    """admin-1 lookup for lat/lon
    
    "admin0"    : United States of America
    "admin1"    : California
    "iso_3166_1": US    https://en.wikipedia.org/wiki/ISO_3166-1
    "iso_3166_2": US-CA https://en.wikipedia.org/wiki/ISO_3166-2
    """
    def __init__(self):
        # Load the GeoJSON FeatureCollection into a GeoDataFrame
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'data',
                     'ne_10m_admin_1_states_provinces',
                     'ne_10m_admin_1_states_provinces.shp')

        gdf = gpd.read_file(p)
        # Ensure it's in WGS84 (lat/lon)
        gdf = gdf.set_crs(epsg=4326)
        self.gdf = gdf
        # Build a spatial index - rtree
        self.sindex = gdf.sindex

    def query(self,lat,lon):
        """
        """
        # Create a Point geometry for the given lat0, lon0
        point = Point(lon, lat)

        # Find potential matches with spatial index
        possible_matches_index = list(self.sindex.intersection(point.bounds))
        possible_matches = self.gdf.iloc[possible_matches_index]
        
        # Further filter using actual geometry
        precise_match = possible_matches[possible_matches.contains(point)]

        if precise_match.empty:
            return 0
        
        return {
            "admin0"    : precise_match.iloc[0]['admin'],
            "admin1"    : precise_match.iloc[0]['name'],
            "iso_3166_1": precise_match.iloc[0]['iso_3166_2'],
            "iso_3166_2": precise_match.iloc[0]['iso_a2'],
        }


if __name__ == "__main__":
    """test"""
    obj = CountryState()
    # Bezau, Niedere
    lat=47.399682
    lon=9.942572
    out = obj.query(lat,lon)
    print(out)