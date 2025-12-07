#!/usr/bin/env python3
"""
Convert HORUS_TW_A and CELLE_ter_TW latitude/longitude coordinates to Taiwan Two-Degree Grid coordinate system (TWD97 TM2 zone 121).

This program reads `HORUS_TW_A.mat` earthquake catalog and `CELLE_ter_TW.mat` grid definition file,
converts coordinates to Taiwan Two-Degree Transverse Mercator projection coordinate system (TWD97 / TM2 zone 121),
and replaces the original latitude/longitude fields with converted coordinates (in kilometers), then writes to new MAT files.
"""

from pathlib import Path
from scipy.io import loadmat, savemat
from pyproj import Transformer
import numpy as np
import argparse


def convert_coordinates(array, lon_idx, lat_idx, transformer, meters_per_km=1000.0):
    """
    Convert latitude/longitude coordinates in array to TWD97 TM2 coordinate system.

    Args:
    - array: Array containing latitude/longitude data
    - lon_idx: Longitude column index
    - lat_idx: Latitude column index
    - transformer: Coordinate transformer
    - meters_per_km: Meters to kilometers ratio (default 1000.0)

    Returns:
    - Converted array
    """
    # Extract latitude/longitude
    lon = array[:, lon_idx]
    lat = array[:, lat_idx]

    # Validate coordinate range (Taiwan region approximately 21-26°N latitude, 119-122°E longitude)
    valid_mask = (lat >= 21) & (lat <= 26) & (lon >= 119) & (lon <= 122)
    if not np.all(valid_mask):
        invalid_count = np.sum(~valid_mask)
        print(f'Warning: Found {invalid_count} records with coordinates outside Taiwan region, these coordinates may lead to inaccurate conversion results.')

    # Convert coordinates
    x_m, y_m = transformer.transform(lon, lat)
    x_km = x_m / meters_per_km
    y_km = y_m / meters_per_km

    # Create modified array copy
    result = array.copy()
    result[:, lon_idx] = x_km  # Replace longitude column with x coordinate (easting)
    result[:, lat_idx] = y_km  # Replace latitude column with y coordinate (northing)

    return result


def convert_celle_coordinates(celle, transformer, meters_per_km=1000.0):
    """
    Convert grid boundary coordinates in CELLE_ter_TW file.

    Args:
    - celle: CELLE_ter_TW array
    - transformer: Coordinate transformer
    - meters_per_km: Meters to kilometers ratio (default 1000.0)

    Returns:
    - Converted CELLE array
    """
    # CELLE_ter_TW.mat format:
    # Column 1: Minimum longitude (°E)
    # Column 2: Maximum longitude (°E)
    # Column 3: Minimum latitude (°N)
    # Column 4: Maximum latitude (°N)

    result = celle.copy()

    # Convert four corner coordinates for each grid cell
    for i in range(celle.shape[0]):
        # Extract grid boundaries
        x_min = celle[i, 0]
        x_max = celle[i, 1]
        y_min = celle[i, 2]
        y_max = celle[i, 3]

        # Check coordinate range
        if not (119 <= x_min <= 122 and 119 <= x_max <= 122 and
                21 <= y_min <= 26 and 21 <= y_max <= 26):
            print(f'Warning: Grid {i+1} coordinates outside Taiwan region, may lead to inaccurate conversion results.')

        # Convert minimum longitude, minimum latitude corner
        x1_m, y1_m = transformer.transform(x_min, y_min)
        # Convert maximum longitude, maximum latitude corner
        x2_m, y2_m = transformer.transform(x_max, y_max)

        # Convert to kilometers and store back to array
        result[i, 0] = x1_m / meters_per_km  # Minimum longitude -> Minimum easting (x)
        result[i, 1] = x2_m / meters_per_km  # Maximum longitude -> Maximum easting (x)
        result[i, 2] = y1_m / meters_per_km  # Minimum latitude -> Minimum northing (y)
        result[i, 3] = y2_m / meters_per_km  # Maximum latitude -> Maximum northing (y)

    return result


def main(horus_infile: Path, celle_infile: Path, horus_outfile: Path, celle_outfile: Path) -> None:
    # Data processing constants
    # Use original MATLAB variable names
    HORUS_VAR = 'HORUS'  # Variable name in HORUS_TW_A.mat
    CELLE_VAR = 'CELLE'  # Variable name in CELLE_ter_TW.mat

    # In .mat files, columns are numbered from 1, but in Python from 0
    # In MATLAB column 7 is latitude (north), column 8 is longitude (east)
    # In Python corresponding indices are 6 for latitude, 7 for longitude
    LAT_COL_IDX = 6  # HORUS latitude column (column 7 in MATLAB, index 6 in Python)
    LON_COL_IDX = 7  # HORUS longitude column (column 8 in MATLAB, index 7 in Python)
    SRC_CRS = 'epsg:4326'  # WGS 84 coordinate system
    DST_CRS = 'epsg:3826'  # TWD97 / TM2 zone 121 coordinate system
    METERS_PER_KM = 1000.0  # Meters per kilometer

    # Create coordinate transformer
    try:
        transformer = Transformer.from_crs(SRC_CRS, DST_CRS, always_xy=True)
    except Exception as e:
        print(f'Error creating coordinate transformer: {e}')
        return

    # Process HORUS_TW_A.mat
    try:
        # Read MATLAB file
        data = loadmat(horus_infile)
        if HORUS_VAR not in data:
            raise KeyError(f'Variable `{HORUS_VAR}` not found in {horus_infile}')

        # Convert coordinates
        horus = data[HORUS_VAR]
        horus_transformed = convert_coordinates(
            horus, LON_COL_IDX, LAT_COL_IDX, transformer, METERS_PER_KM)

        # Save modified data to new MAT file, using original variable name 'HORUS'
        savemat(horus_outfile, {HORUS_VAR: horus_transformed})
        print(f'Data written to {horus_outfile}, variable name {HORUS_VAR} unchanged, original lat/lon replaced with TWD97 TM2 coordinates (km)')
    except Exception as e:
        print(f'Error processing HORUS file: {e}')

    # Process CELLE_ter_TW.mat
    try:
        # Read MATLAB file
        data = loadmat(celle_infile)
        if CELLE_VAR not in data:
            raise KeyError(f'Variable `{CELLE_VAR}` not found in {celle_infile}')

        # Convert coordinates
        celle = data[CELLE_VAR]
        celle_transformed = convert_celle_coordinates(celle, transformer, METERS_PER_KM)

        # Save modified data to new MAT file, using original variable name 'CELLE'
        savemat(celle_outfile, {CELLE_VAR: celle_transformed})
        print(f'Data written to {celle_outfile}, variable name {CELLE_VAR} unchanged, original lat/lon replaced with TWD97 TM2 coordinates (km)')
    except Exception as e:
        print(f'Error processing CELLE file: {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert HORUS and CELLE files lat/lon to TWD97 TM2 zone 121 coordinate system')
    parser.add_argument('--horus-in', type=Path, required=True, help='Input file path for HORUS_TW_A.mat')
    parser.add_argument('--celle-in', type=Path, required=True, help='Input file path for CELLE_ter_TW.mat')
    parser.add_argument('--horus-out', type=Path, required=True, help='Output MAT file path for HORUS')
    parser.add_argument('--celle-out', type=Path, required=True, help='Output MAT file path for CELLE')
    args = parser.parse_args()

    main(args.horus_in, args.celle_in, args.horus_out, args.celle_out)
