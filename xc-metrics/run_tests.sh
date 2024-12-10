#!/bin/bash

# Start Uvicorn server in the background and save its PID
cd ./app
echo "Starting Uvicorn server..."
uvicorn main:app --reload &
UVICORN_PID=$!

# Wait for Uvicorn to fully start up (optional, but helpful to avoid timing issues)
sleep 2

# Run the test script (adjust the path as needed)
cd ../tests
echo "Running test script..."
python3 show_map.py

# After the test script finishes, shut down Uvicorn
echo "Shutting down Uvicorn server..."
kill $UVICORN_PID

# Confirm the server is stopped
wait $UVICORN_PID

echo "Test completed and server shut down."