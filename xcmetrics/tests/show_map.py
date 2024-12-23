#!/usr/bin/env python
import geopandas as gpd
import webbrowser
import os
import requests
import json
import folium

# Define the microservice URL
url = "http://localhost:8000/process"

# Specify the file to be uploaded
# files = {'file': open('xctrack_izoard.igc', 'rb')}
files = {'file': open('2024-01-27-XTR-3ED7C192ECB8-01.IGC', 'rb')}

# Send POST request with the file
response = requests.post(url, files=files)

# Check response
if response.status_code == 200:
    print("GET request successful!")
    json_data = response.json()
    # Save the JSON data to a file for inspection
    with open('dbg_track_analysis.json', 'w') as file:
        json.dump(json_data, file, indent=2)

else:
    print(f"Failed with status code: {response.status_code}")

# convert json to geodataframe
glides = gpd.GeoDataFrame.from_features(json_data["glides"]["features"])
glides.set_crs(epsg=4326, inplace=True)

# Display the first few rows of the GeoDataFrame
print(glides.head())
print(json.dumps(json_data["info"], indent=2))

# Explore the first GeoDataFrame (this returns a folium map object)
m = glides.explore(color='blue')

if {} == json_data["thermals"]:
    print('no thermals')
else:
    thermals = gpd.GeoDataFrame.from_features(json_data["thermals"]["features"])
    thermals.set_crs(epsg=4326, inplace=True)
    thermals.explore(m=m, color='red')
    print(thermals.head())

# set tiles
folium.TileLayer('OpenTopoMap').add_to(m)

# and then we write the map to disk
m.save('dbg_igc_service.html')
# then open it
webbrowser.open('file://' + os.path.realpath('dbg_igc_service.html'))