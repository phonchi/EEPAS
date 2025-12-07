#!/usr/bin/env python3
"""
Coordinate Transformation Utility for Earthquake Catalogs

Converts HORUS earthquake catalog and CELLE grid coordinates between different
coordinate reference systems (CRS). Supports multiple regional projections.

Supported CRS:
    - WGS84 (EPSG:4326): Global lat/lon coordinate system
    - RDN2008 (EPSG:7794): Italy zone projected system (default)
    - TWD97 (EPSG:3826): Taiwan TM2 121°E projected system
    - Custom: Any EPSG code supported by pyproj

Transformed coordinates are in kilometers and replace original lat/lon columns
in the output MATLAB .mat files.

Usage:
    # Default: WGS84 to RDN2008 (Italy)
    python coordinate_transform.py \\
        --horus-in HORUS_Italy.mat \\
        --celle-in CELLE_Italy.mat \\
        --horus-out HORUS_Italy_RDN2008.mat \\
        --celle-out CELLE_Italy_RDN2008.mat

    # Taiwan: WGS84 to TWD97
    python coordinate_transform.py \\
        --horus-in HORUS_Taiwan.mat \\
        --celle-in CELLE_Taiwan.mat \\
        --horus-out HORUS_Taiwan_TWD97.mat \\
        --celle-out CELLE_Taiwan_TWD97.mat \\
        --target-crs epsg:3826 \\
        --region Taiwan

    # Custom EPSG code
    python coordinate_transform.py \\
        --horus-in input.mat \\
        --celle-in grids.mat \\
        --horus-out output.mat \\
        --celle-out grids_out.mat \\
        --target-crs epsg:32633 \\
        --region "Custom Region"
"""

from pathlib import Path
from scipy.io import loadmat, savemat
from pyproj import Transformer
import numpy as np
import argparse
from typing import Tuple, Optional


# Predefined coordinate systems and validation bounds
CRS_PRESETS = {
    'rdn2008': {
        'epsg': 'epsg:7794',
        'name': 'RDN2008 Italy Zone',
        'bounds': {'lat': (35, 48), 'lon': (6, 20)},
        'description': 'Italy national projected coordinate system'
    },
    'twd97': {
        'epsg': 'epsg:3826',
        'name': 'TWD97 TM2 121°E',
        'bounds': {'lat': (21, 26), 'lon': (119, 123)},
        'description': 'Taiwan projected coordinate system (Transverse Mercator 2-degree)'
    },
    'wgs84': {
        'epsg': 'epsg:4326',
        'name': 'WGS84',
        'bounds': {'lat': (-90, 90), 'lon': (-180, 180)},
        'description': 'Global geographic coordinate system (lat/lon)'
    }
}


def get_crs_info(crs_key: str) -> dict:
    """
    Get coordinate system information from preset or custom EPSG code.

    Args:
        crs_key: CRS preset key ('rdn2008', 'twd97') or EPSG code ('epsg:3826')

    Returns:
        dict: CRS information including EPSG code, name, and bounds
    """
    crs_lower = crs_key.lower()

    # Check if it's a preset
    if crs_lower in CRS_PRESETS:
        return CRS_PRESETS[crs_lower]

    # If starts with 'epsg:', treat as custom EPSG code
    if crs_lower.startswith('epsg:'):
        return {
            'epsg': crs_lower,
            'name': f'Custom {crs_key.upper()}',
            'bounds': {'lat': (-90, 90), 'lon': (-180, 180)},
            'description': 'Custom coordinate reference system'
        }

    raise ValueError(f'Unknown coordinate system: {crs_key}. Supported presets: {list(CRS_PRESETS.keys())} or custom EPSG code (e.g., epsg:3826)')


def validate_coordinates(lon: np.ndarray, lat: np.ndarray, bounds: dict,
                        region_name: str = "region") -> Tuple[bool, int]:
    """
    Validate coordinates are within expected regional bounds.

    Args:
        lon: Longitude array (degrees East)
        lat: Latitude array (degrees North)
        bounds: Dictionary with 'lat' and 'lon' tuples (min, max)
        region_name: Name of region for warning messages

    Returns:
        Tuple[bool, int]: (all_valid, invalid_count)
    """
    lat_min, lat_max = bounds['lat']
    lon_min, lon_max = bounds['lon']

    valid_mask = (lat >= lat_min) & (lat <= lat_max) & (lon >= lon_min) & (lon <= lon_max)
    invalid_count = np.sum(~valid_mask)

    if invalid_count > 0:
        print(f'⚠️  Warning: {invalid_count} coordinates out of bounds for {region_name}, transformation may be inaccurate')
        invalid_lats = lat[~valid_mask]
        invalid_lons = lon[~valid_mask]
        print(f'   Invalid range: lat [{invalid_lats.min():.2f}, {invalid_lats.max():.2f}]°N, '
              f'lon [{invalid_lons.min():.2f}, {invalid_lons.max():.2f}]°E')
        print(f'   Expected range: lat [{lat_min}, {lat_max}]°N, lon [{lon_min}, {lon_max}]°E')
        return False, invalid_count

    return True, 0


def convert_coordinates(array: np.ndarray, lon_idx: int, lat_idx: int,
                       transformer: Transformer, bounds: dict,
                       region_name: str = "region",
                       meters_per_km: float = 1000.0) -> np.ndarray:
    """
    Convert lat/lon coordinates in array to projected coordinates.

    Args:
        array: Array containing lat/lon data
        lon_idx: Longitude column index
        lat_idx: Latitude column index
        transformer: pyproj Transformer object
        bounds: Coordinate validation bounds
        region_name: Region name for validation messages
        meters_per_km: Meters to kilometers conversion factor (default: 1000.0)

    Returns:
        np.ndarray: Transformed array with coordinates in km

    Note:
        Validates coordinates are within regional bounds and prints warnings
        for out-of-range coordinates.
    """
    # Extract lon/lat
    lon = array[:, lon_idx]
    lat = array[:, lat_idx]

    # Validate coordinate range
    validate_coordinates(lon, lat, bounds, region_name)

    # Transform coordinates (lon, lat) -> (easting x, northing y)
    x_m, y_m = transformer.transform(lon, lat)
    x_km = x_m / meters_per_km
    y_km = y_m / meters_per_km

    # Create modified array copy
    result = array.copy()
    result[:, lon_idx] = x_km  # Replace lon column with x (easting, km)
    result[:, lat_idx] = y_km  # Replace lat column with y (northing, km)

    return result


def convert_celle_coordinates(celle: np.ndarray, transformer: Transformer,
                              bounds: dict, region_name: str = "region",
                              meters_per_km: float = 1000.0) -> np.ndarray:
    """
    Convert CELLE grid boundary coordinates.

    Args:
        celle: CELLE array (each row: lon_min, lon_max, lat_min, lat_max)
        transformer: pyproj Transformer object
        bounds: Coordinate validation bounds
        region_name: Region name for validation messages
        meters_per_km: Meters to kilometers conversion factor (default: 1000.0)

    Returns:
        np.ndarray: Transformed CELLE array (x_min, x_max, y_min, y_max in km)

    Note:
        CELLE format columns:
            - Column 0: Minimum longitude (°E)
            - Column 1: Maximum longitude (°E)
            - Column 2: Minimum latitude (°N)
            - Column 3: Maximum latitude (°N)
    """
    result = celle.copy()
    lat_min_bound, lat_max_bound = bounds['lat']
    lon_min_bound, lon_max_bound = bounds['lon']

    # Transform four corners of each grid cell
    for i in range(celle.shape[0]):
        # Extract grid boundaries
        lon_min = celle[i, 0]
        lon_max = celle[i, 1]
        lat_min = celle[i, 2]
        lat_max = celle[i, 3]

        # Check coordinate range
        if not (lon_min_bound <= lon_min <= lon_max_bound and
                lon_min_bound <= lon_max <= lon_max_bound and
                lat_min_bound <= lat_min <= lat_max_bound and
                lat_min_bound <= lat_max <= lat_max_bound):
            print(f'⚠️  Warning: Grid {i+1} coordinates out of bounds for {region_name}, transformation may be inaccurate')
            print(f'   Grid range: lon [{lon_min:.2f}, {lon_max:.2f}]°E, '
                  f'lat [{lat_min:.2f}, {lat_max:.2f}]°N')

        # Transform min lon, min lat corner
        x1_m, y1_m = transformer.transform(lon_min, lat_min)
        # Transform max lon, max lat corner
        x2_m, y2_m = transformer.transform(lon_max, lat_max)

        # Convert to km and store back to array
        result[i, 0] = x1_m / meters_per_km  # Min lon -> Min easting (x)
        result[i, 1] = x2_m / meters_per_km  # Max lon -> Max easting (x)
        result[i, 2] = y1_m / meters_per_km  # Min lat -> Min northing (y)
        result[i, 3] = y2_m / meters_per_km  # Max lat -> Max northing (y)

    return result


def main(horus_infile: Optional[Path], celle_infile: Optional[Path],
         horus_outfile: Optional[Path], celle_outfile: Optional[Path],
         target_crs: str = 'rdn2008', region_name: Optional[str] = None) -> None:
    """
    Main function to convert HORUS and CELLE coordinates between CRS.

    Args:
        horus_infile: Input HORUS catalog .mat file path (optional)
        celle_infile: Input CELLE grid .mat file path (optional)
        horus_outfile: Output HORUS .mat file path (optional)
        celle_outfile: Output CELLE .mat file path (optional)
        target_crs: Target coordinate system ('rdn2008', 'twd97', or 'epsg:XXXX')
        region_name: Custom region name for messages (optional)

    Returns:
        None: Writes transformed data to output files and prints status

    Note:
        HORUS format columns:
            - Column 7 (index 6): Latitude (°N)
            - Column 8 (index 7): Longitude (°E)

        After transformation, these columns contain:
            - Column 7 (index 6): Northing Y (km)
            - Column 8 (index 7): Easting X (km)
    """
    # Get CRS information
    crs_info = get_crs_info(target_crs)
    if region_name is None:
        region_name = crs_info['name']

    print('='*60)
    print('Coordinate Transformation Tool')
    print('='*60)
    print(f'Target Coordinate System: {crs_info["name"]} ({crs_info["epsg"]})')
    print(f'Description: {crs_info["description"]}')
    print(f'Region: {region_name}')
    print('='*60)

    # Data processing constants
    HORUS_VAR = 'HORUS'  # Variable name in HORUS.mat
    CELLE_VAR = 'CELLE'  # Variable name in CELLE.mat

    # HORUS catalog column indices
    LAT_COL_IDX = 6  # Latitude column index (column 7)
    LON_COL_IDX = 7  # Longitude column index (column 8)

    SRC_CRS = 'epsg:4326'  # WGS 84 coordinate system (source)
    DST_CRS = crs_info['epsg']  # Target coordinate system
    METERS_PER_KM = 1000.0  # Meters per kilometer

    # Create coordinate transformer
    try:
        transformer = Transformer.from_crs(SRC_CRS, DST_CRS, always_xy=True)
        print(f'\n✓ Coordinate transformer created: {SRC_CRS} -> {DST_CRS}')
    except Exception as e:
        print(f'❌ Error creating coordinate transformer: {e}')
        return

    # Process HORUS earthquake catalog
    if horus_infile and horus_outfile:
        if horus_infile.exists():
            try:
                print(f'\nProcessing HORUS file: {horus_infile}')

                # Read MATLAB file
                data = loadmat(horus_infile)
                if HORUS_VAR not in data:
                    raise KeyError(f'Variable `{HORUS_VAR}` not found in {horus_infile}')

                horus = data[HORUS_VAR]
                print(f'  Original data shape: {horus.shape}')
                print(f'  Coordinate range:')
                print(f'    Latitude: [{horus[:, LAT_COL_IDX].min():.2f}, {horus[:, LAT_COL_IDX].max():.2f}]°N')
                print(f'    Longitude: [{horus[:, LON_COL_IDX].min():.2f}, {horus[:, LON_COL_IDX].max():.2f}]°E')

                # Transform coordinates
                horus_transformed = convert_coordinates(
                    horus, LON_COL_IDX, LAT_COL_IDX, transformer,
                    crs_info['bounds'], region_name, METERS_PER_KM)

                print(f'  Transformed coordinate range (km):')
                print(f'    Easting (X): [{horus_transformed[:, LON_COL_IDX].min():.2f}, {horus_transformed[:, LON_COL_IDX].max():.2f}] km')
                print(f'    Northing (Y): [{horus_transformed[:, LAT_COL_IDX].min():.2f}, {horus_transformed[:, LAT_COL_IDX].max():.2f}] km')

                # Save transformed data
                savemat(horus_outfile, {HORUS_VAR: horus_transformed})
                print(f'✓ Data written to {horus_outfile}')
                print(f'  Variable name `{HORUS_VAR}` preserved, original lat/lon replaced with projected coordinates (km)')

            except Exception as e:
                print(f'❌ Error processing HORUS file: {e}')
        else:
            print(f'⚠️  HORUS file not found: {horus_infile}, skipping')
    else:
        if not horus_infile:
            print('\nNo HORUS input file specified, skipping HORUS transformation')

    # Process CELLE grid definition
    if celle_infile and celle_outfile:
        if celle_infile.exists():
            try:
                print(f'\nProcessing CELLE file: {celle_infile}')

                # Read MATLAB file
                data = loadmat(celle_infile)
                if CELLE_VAR not in data:
                    raise KeyError(f'Variable `{CELLE_VAR}` not found in {celle_infile}')

                celle = data[CELLE_VAR]
                print(f'  Original data shape: {celle.shape}')
                print(f'  Number of grids: {celle.shape[0]}')
                print(f'  Coordinate range:')
                print(f'    Latitude: [{celle[:, 2].min():.2f}, {celle[:, 3].max():.2f}]°N')
                print(f'    Longitude: [{celle[:, 0].min():.2f}, {celle[:, 1].max():.2f}]°E')

                # Transform coordinates
                celle_transformed = convert_celle_coordinates(
                    celle, transformer, crs_info['bounds'], region_name, METERS_PER_KM)

                print(f'  Transformed coordinate range (km):')
                print(f'    Easting (X): [{celle_transformed[:, 0].min():.2f}, {celle_transformed[:, 1].max():.2f}] km')
                print(f'    Northing (Y): [{celle_transformed[:, 2].min():.2f}, {celle_transformed[:, 3].max():.2f}] km')

                # Save transformed data
                savemat(celle_outfile, {CELLE_VAR: celle_transformed})
                print(f'✓ Data written to {celle_outfile}')
                print(f'  Variable name `{CELLE_VAR}` preserved, original lat/lon replaced with projected coordinates (km)')

            except Exception as e:
                print(f'❌ Error processing CELLE file: {e}')
        else:
            print(f'⚠️  CELLE file not found: {celle_infile}, skipping')
    else:
        if not celle_infile:
            print('\nNo CELLE input file specified, skipping CELLE transformation')

    print('\n' + '='*60)
    print('✓ Coordinate transformation completed!')
    print('='*60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Transform coordinate systems for HORUS and CELLE files (supports multiple projected coordinate systems)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

1. Italy (WGS84 -> RDN2008, default):
  python coordinate_transform.py \\
    --horus-in HORUS_Italy.mat \\
    --celle-in CELLE_Italy.mat \\
    --horus-out HORUS_Italy_RDN2008.mat \\
    --celle-out CELLE_Italy_RDN2008.mat

2. Taiwan (WGS84 -> TWD97):
  python coordinate_transform.py \\
    --horus-in HORUS_Taiwan.mat \\
    --celle-in CELLE_Taiwan.mat \\
    --horus-out HORUS_Taiwan_TWD97.mat \\
    --celle-out CELLE_Taiwan_TWD97.mat \\
    --target-crs twd97 \\
    --region Taiwan

3. Custom EPSG code:
  python coordinate_transform.py \\
    --horus-in input.mat \\
    --horus-out output.mat \\
    --target-crs epsg:32633 \\
    --region "Custom Region"

Supported default coordinate systems:
  - rdn2008: RDN2008 Italy Zone (EPSG:7794) [default]
  - twd97: TWD97 TM2 121°E (EPSG:3826)
  - or any EPSG code (e.g., epsg:32633)

Notes:
  - Input file coordinates must be WGS84 lat/lon (°N, °E)
  - Output file coordinates will be in projected coordinates (km)
  - HORUS file column 7 (index 6) is latitude, column 8 (index 7) is longitude
  - CELLE file format: [lon_min, lon_max, lat_min, lat_max]
  - Can transform HORUS or CELLE separately (omit the other file parameter)
        """
    )
    parser.add_argument('--horus-in', type=Path,
                       help='Input HORUS earthquake catalog file path (.mat format)')
    parser.add_argument('--celle-in', type=Path,
                       help='Input CELLE grid definition file path (.mat format)')
    parser.add_argument('--horus-out', type=Path,
                       help='Output HORUS MAT file path')
    parser.add_argument('--celle-out', type=Path,
                       help='Output CELLE MAT file path')
    parser.add_argument('--target-crs', type=str, default='rdn2008',
                       help='Target coordinate system (rdn2008, twd97, or epsg:XXXX) [default: rdn2008]')
    parser.add_argument('--region', type=str,
                       help='Region name (for message display)')

    args = parser.parse_args()

    # Validate input/output pairs
    if args.horus_in and not args.horus_out:
        parser.error('--horus-in must be paired with --horus-out')
    if args.horus_out and not args.horus_in:
        parser.error('--horus-out must be paired with --horus-in')
    if args.celle_in and not args.celle_out:
        parser.error('--celle-in must be paired with --celle-out')
    if args.celle_out and not args.celle_in:
        parser.error('--celle-out must be paired with --celle-in')

    if not args.horus_in and not args.celle_in:
        parser.error('At least --horus-in or --celle-in must be specified')

    main(args.horus_in, args.celle_in, args.horus_out, args.celle_out,
         args.target_crs, args.region)
