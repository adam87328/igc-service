from fastapi import HTTPException
import subprocess
import json
import sys

def igc_xc_score(data):
    """igc-xc-score wrapper
    
    https://github.com/mmomtchev/igc-xc-score
    """

    # choose executable based on OS
    if sys.platform == 'darwin': # macos
        bin = "./igc-xc-score-macos"
    else:
        bin = "./igc-xc-score-linux"

    program = [bin, 
        "quiet=true", 
        "pipe=true", 
        "noflight=true",
        "scoring=XContest"]
    
    # Start the process
    process = subprocess.Popen(
        program, 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Enable text mode (for string input/output instead of bytes)
    )

    # Send input data and get the output
    stdout, stderr = process.communicate(input=data)

    # Check if any error occurred
    if stderr:
        raise HTTPException(
            status_code=500, # Internal Server Error
            detail=f"Internal Error: igc-xc-score: {stderr}")
    else:
        d = json.loads(stdout)

    # merge properties
    for key in ['distance', 'multiplier', 'penalty']:
        d['geojson']['properties'][key] = d['solution']['bestSolution'][key]
    # camel case conversion
    d['geojson']['properties']['closing_distance'] = \
        d['solution']['bestSolution']['closingDistance']
    
    # compute some dependent properties

    # feature names : linear index dict
    ids = {}
    for [idx, item] in enumerate(d['geojson']['features']):
        ids[item['id']] = idx
    
    # average XC speed of entire flight: distance / airtime
    t1 = d['geojson']['features'][ids['launch0']]['properties']['timestamp']
    t2 = d['geojson']['features'][ids['land0']]['properties']['timestamp']
    t_air = (t2-t1)/1000 # seconds
    v_air = d['geojson']['properties']['distance'] / (t_air/3600) # km/h
    d['geojson']['properties']['airtime'] = t_air
    d['geojson']['properties']['xc_speed_airtime'] = v_air

    # extract time spent on section of flight relevant for scoring
    if 'cp_in' in ids:
        t1 = d['geojson']['features'][ids['cp_in']]['properties']['timestamp']
        t2 = d['geojson']['features'][ids['cp_out']]['properties']['timestamp']
    elif 'ep_start' in ids:
        t1 = d['geojson']['features'][ids['ep_start']]['properties']['timestamp']
        t2 = d['geojson']['features'][ids['ep_finish']]['properties']['timestamp']
    else:
        Exception('found neither cp_in nor ep_start')

    # average XC speed over section of flight relevant for scoring, km/h
    t_route = (t2-t1)/1000 # seconds
    v_route = d['geojson']['properties']['distance'] / (t_route/3600)
    
    d['geojson']['properties']['route_time'] = t_route
    d['geojson']['properties']['xc_speed_route'] = v_route

    # print(json.dumps(d['geojson']['properties'],indent=2))
    return d