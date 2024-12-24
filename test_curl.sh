#!/bin/bash

# xcmetrics 8081
# geolookup 8082
# xcscore   8083

curl -F "file=@./testdata/valid_xctrack.igc" http://127.0.0.1:8081/ | python -m json.tool
 
curl -F "file=@./testdata/valid_xctrack.igc" http://127.0.0.1:8083/ | python -m json.tool