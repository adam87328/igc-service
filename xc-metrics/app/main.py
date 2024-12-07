#!/usr/bin/env python
import sys

sys.path.append('./submodules/igc_lib')
import igc_lib
import geopandas as gpd
import matplotlib.pyplot as plt
import webbrowser
import os
from shapely.geometry import LineString
import numpy as np

class igcLibCfg(igc_lib.FlightParsingConfig):
    min_time_for_bearing_change = 2.0

flight = igc_lib.Flight.create_from_file('./data/izoard1.igc',igcLibCfg)

# Convert the array of coordinates to a LineString
line = []
for thermal in flight.thermals:
    line.append( LineString(np.array([[fix.lon, fix.lat] for fix in thermal.fixes])) )

# Create a GeoDataFrame with the LineString geometry
gdf_thermals = gpd.GeoDataFrame({
    'geometry': line, 
    'direction': [thermal.direction for thermal in flight.thermals],
    'alt_change': [thermal.alt_change() for thermal in flight.thermals],
    'vertical_velocity': [thermal.vertical_velocity() for thermal in flight.thermals],
    })
gdf_thermals.set_crs(epsg=4326, inplace=True)


# Convert the array of coordinates to a LineString
line = []
for glide in flight.glides:
    line.append( LineString(np.array([[fix.lon, fix.lat] for fix in glide.fixes])) )
# Create a GeoDataFrame with the LineString geometry
gdf_glides = gpd.GeoDataFrame({
    'geometry': line, 
    'alt_change': [glide.alt_change() for glide in flight.glides],
    'glide_ratio': [glide.glide_ratio() for glide in flight.glides],
    })
gdf_glides.set_crs(epsg=4326, inplace=True)

# Explore the first GeoDataFrame (this returns a folium map object)
m = gdf_thermals.explore(color='red')
gdf_glides.explore(m=m, color='blue')
# and then we write the map to disk
m.save('my_map.html')
# then open it
webbrowser.open('file://' + os.path.realpath('my_map.html'))


