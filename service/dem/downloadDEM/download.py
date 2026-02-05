import subprocess
import os

# -----------------------------------------------------------------------------
# Simple bounding box / tile
# -----------------------------------------------------------------------------
# Example: Choose the tile with its lower-left corner at:
#   Latitude  = 47°N  (so tile covers 47–48°N)
#   Longitude = 9°E   (so tile covers 9–10°E)
lat_idx = 47
lon_idx = 9

# Naming convention components
ns = "N" if lat_idx >= 0 else "S"
lat_tag = f"{ns}{abs(lat_idx):02d}_00"

ew = "E" if lon_idx >= 0 else "W"
lon_tag = f"{ew}{abs(lon_idx):03d}_00"

# Construct S3 object key prefix
tile_base = f"Copernicus_DSM_COG_10_{lat_tag}_{lon_tag}_DEM"
s3_key = f"{tile_base}/{tile_base}.tif"

# Output directory and file
outdir = "demo_tile"
os.makedirs(outdir, exist_ok=True)
output_path = os.path.join(outdir, f"{tile_base}.tif")

print("Attempting to download:")
print(" S3 key:", s3_key)
print(" Output:", output_path)

# -----------------------------------------------------------------------------
# Download from AWS public bucket using awscli with no credentials
# -----------------------------------------------------------------------------
cmd = [
    "aws", "s3", "cp",
    f"s3://copernicus-dem-30m/{s3_key}",
    output_path,
    "--no-sign-request"
]

try:
    subprocess.run(cmd, check=True)
    print("Download successful!")
except subprocess.CalledProcessError as e:
    print("Download failed:", e)