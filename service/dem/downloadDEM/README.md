# Copernicus DSM Tile Downloader

This script downloads Copernicus Digital Surface Model (DSM) tiles from AWS S3 public bucket.

## Requirements

- Python 3
- AWS CLI installed and in PATH
- No AWS credentials needed (uses `--no-sign-request`)

### Install AWS CLI

```bash
# On Ubuntu/Debian
sudo apt-get install awscli

# On macOS
brew install awscli

# Via pip
pip install awscli
```

## Usage

### Download All Alps Tiles

Download all tiles covering the Alps region (43°N-48°N, 5°E-17°E):

```bash
python download.py /path/to/dem_tiles
```

This will download approximately 60 tiles (5 latitude × 12 longitude degrees).

### Download Single Tile

Download a specific tile:

```bash
python download.py --tile 47 9 /path/to/dem_tiles
```

This downloads the tile covering 47°N-48°N, 9°E-10°E.

### Default Output Directory

If no path is specified, tiles are saved to `./dem_tiles`:

```bash
python download.py
```

## Tile Coverage

The Alps region tiles cover:
- **Latitude**: 43°N to 48°N
- **Longitude**: 5°E to 17°E

This includes:
- Swiss Alps
- French Alps
- Italian Alps
- Austrian Alps
- Parts of Germany and Slovenia

## Tile Naming Convention

Tiles follow the Copernicus naming format:
```
Copernicus_DSM_COG_10_N47_00_E009_00_DEM.tif
```

Where:
- `N47` = 47°N latitude (lower-left corner)
- `E009` = 9°E longitude (lower-left corner)
- Each tile covers 1°×1° area

## Data Source

- **Dataset**: Copernicus DEM GLO-30 (30m resolution)
- **Format**: Cloud-Optimized GeoTIFF (COG)
- **S3 Bucket**: `s3://copernicus-dem-30m/` (public, no authentication)
- **Resolution**: ~30 meters
- **Vertical Accuracy**: Typically 2-4 meters (varies by region)

## Storage Requirements

- Each tile: ~40-100 MB (varies by terrain complexity)
- Full Alps region (~60 tiles): ~3-6 GB total

## Notes

- The script skips tiles that already exist in the output directory
- Download failures are reported but don't stop the process
- Some tiles may not exist if they cover only ocean
- DSM (Digital Surface Model) includes vegetation and buildings
  - For bare earth elevation, consider DTM (Digital Terrain Model) instead

## Example Output

```
Downloading Copernicus DSM tiles for the Alps region
  Latitude range: 43°N to 48°N
  Longitude range: 5°E to 17°E
  Output directory: /data/dem_tiles

Downloading tile 43°N, 5°E...
  S3 key: Copernicus_DSM_COG_10_N43_00_E005_00_DEM/Copernicus_DSM_COG_10_N43_00_E005_00_DEM.tif
  Output: /data/dem_tiles/Copernicus_DSM_COG_10_N43_00_E005_00_DEM.tif
  ✓ Download successful!

...

Download complete: 58/60 tiles successful
```

## Troubleshooting

### "command not found: aws"
Install AWS CLI (see Requirements section).

### "Unable to locate credentials"
This should not happen since we use `--no-sign-request`. If it does, check your AWS CLI installation.

### Download failures
Some tiles might not exist in the S3 bucket. This is normal for tiles that are entirely over ocean.

### Slow downloads
Downloads are sequential. For faster downloads, consider using:
- AWS CLI's `sync` command with parallel transfers
- A download manager
- Downloading from a region closer to the S3 bucket (US-East)
