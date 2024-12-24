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
        return json.loads(stdout)