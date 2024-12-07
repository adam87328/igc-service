#!/usr/bin/env python
import geopandas as gpd
import matplotlib.pyplot as plt
import webbrowser
import os

# Load the GeoJSON file into a GeoDataFrame
gdf = gpd.read_file('./submodules/flight.json')

# Display the first few rows of the GeoDataFrame
print(gdf.head())

# Get information about the data (geometry, columns)
print(gdf.info())

## Plot the GeoJSON data
#fig, ax = plt.subplots()
#gdf.plot()
#plt.show()

# Explore the first GeoDataFrame (this returns a folium map object)
m = gdf.explore(color='blue')
# and then we write the map to disk
m.save('explore_geojson.html')
# then open it
webbrowser.open('file://' + os.path.realpath('explore_geojson.html'))


