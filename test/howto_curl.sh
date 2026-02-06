#!/bin/bash

# xcmetrics 8081
curl -F "file=@./testdata/valid_xctrack.igc" http://127.0.0.1:8081/ | python -m json.tool

# dem       8004
curl -H "Content-Type: application/json" -d @xcmetrics_timeseries.json http://127.0.0.1:8084/ | python -m json.tool

# xcscore   8083
curl -F "file=@./testdata/valid_xctrack.igc" http://127.0.0.1:8083/ | python -m json.tool

# geolookup 8082
curl http://127.0.0.1:8082/nearest_town?lat=47.399682&lon=9.942572 | python -m json.tool
curl http://127.0.0.1:8082/takeoffdb?lat=47.399682&lon=9.942572 | python -m json.tool
curl http://127.0.0.1:8082/admin1?lat=47.399682&lon=9.942572 | python -m json.tool