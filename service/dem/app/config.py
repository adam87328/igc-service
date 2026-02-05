#!/usr/bin/env python3
"""
Configuration for DEM service.
"""

import os
from pathlib import Path

# DEM tiles directory - can be configured via environment variable
# Defaults to mounted volume path in Docker or tests/resources for development
_default_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tests",
    "resources"
)

DEM_TILES_DIR = os.environ.get("DEM_TILES_DIR", _default_path)

# Validate that the directory exists
if not os.path.isdir(DEM_TILES_DIR):
    import warnings
    warnings.warn(
        f"DEM_TILES_DIR '{DEM_TILES_DIR}' does not exist. "
        "Service will return None for elevations."
    )
