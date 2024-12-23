import os
import geopandas as gpd
from shapely.geometry import Point

class NamedTakeoff:

    def __init__(self):
        # Load the GeoJSON FeatureCollection into a GeoDataFrame
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'data','paraglidingearth','pgEarthSpots.json') 
        gdf = gpd.read_file(p)
        # Convert the GeoDataFrame to a projected CRS to measure distances in meters
        # WGS 84 (lat/lon) is EPSG:4326, and we convert to a metric CRS like EPSG:3857
        gdf = gdf.set_crs(epsg=4326)  # Ensure it's in WGS84 (lat/lon)
        gdf = gdf.to_crs(epsg=3857)   # Convert to a metric CRS for distance calculations
        self.gdf = gdf

    def query(self,lat,lon,search_radius):
        """Extract named takeoff and landing locations from database

        Database is extracted from paraglidingearth.com

        search_radius: Radius in meters around lat, lon
        """
        # Create a Point geometry for the given lat0, lon0
        takeoff = Point(lon, lat)

        # Convert the reference point to the same CRS
        takeoff = gpd.GeoSeries([takeoff], crs='EPSG:4326').to_crs(epsg=3857).iloc[0]

        # Calculate distances from the reference point to each feature
        self.gdf['distance'] = self.gdf.geometry.distance(takeoff)

        # Filter the features within the specified distance
        nearby = self.gdf[self.gdf['distance'] <= search_radius]
        nearby = nearby.sort_values(by='distance', ascending=True)
        
        if nearby.empty:
            out = {
                "name"     : "",
                "country"  : "",
                "dist"     : 0, # meters
                "db_lat"   : 0, # deg
                "db_lon"   : 0, # deg
            }
        else:
            out = {
                "name"     : nearby.iloc[0]['name'],
                "country"  : nearby.iloc[0]['countryCode'].upper(),
                "dist"     : nearby.iloc[0]['distance'],
                "db_lat"   : nearby.to_crs(epsg=4326).iloc[0].geometry.y,
                "db_lon"   : nearby.to_crs(epsg=4326).iloc[0].geometry.x,
            }

        return out

if __name__ == "__main__":
    """test"""
    obj = NamedTakeoff()
    # Bezau, Niedere
    lat=47.399682
    lon=9.942572
    out = obj.query(lat,lon)
    print(out)