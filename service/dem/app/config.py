#!/usr/bin/env python3
"""
Configuration for DEM service.
"""

import os
from pathlib import Path

# DEM tiles directory - can be configured via environment variable
# Defaults to mounted volume path in Docker or tests/resources for development
DEM_TILES_DIR = os.environ.get(
    "DEM_TILES_DIR",
    str(Path(__file__).parent.parent / "tests" / "resources")
)

# Validate that the directory exists
if not os.path.isdir(DEM_TILES_DIR):
    import warnings
    warnings.warn(
        f"DEM_TILES_DIR '{DEM_TILES_DIR}' does not exist. "
        "Service will return None for elevations."
    )
