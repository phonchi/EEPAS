import scipy.io
import pandas as pd
import numpy as np
import csep
from csep.utils import datasets, time_utils
from datetime import datetime, timezone
from tqdm import tqdm
import os

# ----------------------------------------------------------------------
# Function definitions (From your dataset (2).py, with modifications)
# ----------------------------------------------------------------------

def extract_period_forecast(period_idx, forecast_data, num_magnitude_steps, magnitude_bins, num_regions, cell_bounds):
    """
    Extract earthquake forecast data for specified 3-month period.
    (This function is essentially the same as your version)

    Args:
        period_idx: Period index (starting from 1) (int)
        forecast_data: Complete forecast data matrix (ndarray)
        num_magnitude_steps: Number of magnitude bins (int)
    magnitude_bins : list
        List of magnitude bin tuples [(m0, m1), ...]
    num_regions : int
        Number of spatial regions
    cell_bounds : DataFrame
        Already converted to lon/lat DataFrame

    Returns:
    pd.DataFrame
        Forecast data for the specified period
    """
    start_idx = (period_idx - 1) * num_magnitude_steps
    end_idx = start_idx + num_magnitude_steps

    if start_idx >= forecast_data.shape[0] or start_idx < 0:
        raise ValueError(f"period {period_idx} out of range")

    period_rows = forecast_data[start_idx:end_idx]

    rows = []
    for mag_idx in range(min(len(period_rows), num_magnitude_steps)):
        mag_0, mag_1 = magnitude_bins[mag_idx]
        mag_row = period_rows[mag_idx]
        period_number = int(mag_row[0])

        for region_idx in range(min(num_regions, len(cell_bounds))):
            rate = float(mag_row[region_idx + 1])
            # Read boundaries already converted to lon/lat
            region = cell_bounds.iloc[region_idx]

            rows.append({
                'LON_0': float(region['LON_0']), # Bounding Box Minimum longitude
                'LON_1': float(region['LON_1']), # Bounding Box Maximum longitude
                'LAT_0': float(region['LAT_0']), # Bounding Box Minimum latitude
                'LAT_1': float(region['LAT_1']), # Bounding Box Maximum latitude
                'Z_0': 0.0,
                'Z_1': 30.0,
                'MAG_0': mag_0,
                'MAG_1': mag_1,
                'RATE': rate,
                'FLAG': 1,
                'PERIOD': period_number
            })

    return pd.DataFrame(rows)

# --- This is the new, corrected create_subgrids function ---

def create_subgrids_spatial(data, grid_resolution=0.1):
    """
    Divide large grid (possibly irregular lon/lat boundaries) into 0.1x0.1 sub-grids.

    Using 'Centroid-in-Bounding-Box' method for spatial downscaling.

    Args:
        data: Coarse grid forecast data (pd.DataFrame)
        grid_resolution: Sub-grid resolution in degrees (default: 0.1) (float, optional)

    Returns:
    pd.DataFrame
        Downscaled forecast data with sub-grids
    """
    print(f"Downscaling large grids to {grid_resolution}°×{grid_resolution}° sub-grids (Using spatial method)...")

    new_rows = []

    # Tqdm for displaying processing progress
    for _, row in tqdm(data.iterrows(), total=len(data), desc="Processing sub-grids"):
        # Get lon/lat bounding box of large grid
        coarse_lon_0 = row['LON_0']
        coarse_lon_1 = row['LON_1']
        coarse_lat_0 = row['LAT_0']
        coarse_lat_1 = row['LAT_1']
        coarse_rate = row['RATE']

        mag_0 = row['MAG_0']
        mag_1 = row['MAG_1']
        period = row.get('PERIOD', 1)

        # Find grid range that completely covers this bounding box with 0.1° grids
        # Round down to 0.1 multiples
        sub_lon_start_grid = np.floor(coarse_lon_0 * 10) / 10
        # Round up to 0.1 multiples
        sub_lon_end_grid = np.ceil(coarse_lon_1 * 10) / 10
        sub_lat_start_grid = np.floor(coarse_lat_0 * 10) / 10
        sub_lat_end_grid = np.ceil(coarse_lat_1 * 10) / 10

        # Generate 0.1° candidate starting points for sub-grids
        sub_lons = np.arange(sub_lon_start_grid, sub_lon_end_grid, grid_resolution)
        sub_lats = np.arange(sub_lat_start_grid, sub_lat_end_grid, grid_resolution)

        # Find all sub-grids whose center points fall within the large grid bounding box interior
        sub_cells_in_this_coarse_cell = []
        for lon_0 in sub_lons:
            for lat_0 in sub_lats:
                # Calculate center point of 0.1x0.1 sub-grid
                lon_center = lon_0 + (grid_resolution / 2)
                lat_center = lat_0 + (grid_resolution / 2)

                # Check if center point is within bounding box interior
                # Note: Lon/lat ranges are typically left-closed, right-open [lon_min, lon_max)
                if (coarse_lon_0 <= lon_center < coarse_lon_1) and \
                   (coarse_lat_0 <= lat_center < coarse_lat_1):
                    sub_cells_in_this_coarse_cell.append((lon_0, lat_0))

        num_subcells = len(sub_cells_in_this_coarse_cell)
        # Divide large grid's RATE evenly among all found sub-grids
        subcell_rate = coarse_rate / num_subcells if num_subcells > 0 else 0

        if num_subcells == 0:
            # If large grid is too small, may have no 0.1° grid center points falling within
            # print(f"Warning: Grid ({coarse_lon_0:.2f}, {coarse_lat_0:.2f}) did not find corresponding 0.1° sub-grid center points.")
            continue

        # Add new row for each valid sub-grid
        for lon_0, lat_0 in sub_cells_in_this_coarse_cell:
            new_rows.append({
                'LON_0': round(lon_0, 2), # Round to avoid floating point issues
                'LON_1': round(lon_0 + grid_resolution, 2),
                'LAT_0': round(lat_0, 2),
                'LAT_1': round(lat_0 + grid_resolution, 2),
                'Z_0': 0.0,
                'Z_1': 30.0,
                'MAG_0': mag_0,
                'MAG_1': mag_1,
                'RATE': subcell_rate,
                'FLAG': 1,
                'PERIOD': period
            })

    return pd.DataFrame(new_rows)


def generate_all_periods_forecast(forecast_data, num_magnitude_steps, magnitude_bins, num_regions, cell_bounds, start_period=1, end_period=None):
    """
    Generate forecast data for all periods, summing rates across different periods for same grid and magnitude.
    (This function now calls the new create_subgrids_spatial)

    Args:
        forecast_data: Complete forecast data matrix (ndarray)
        num_magnitude_steps: Number of magnitude bins (int)
        magnitude_bins: List of magnitude bin tuples (list)
    num_regions : int
        Number of spatial regions
    cell_bounds : DataFrame
        Grid boundary definitions
    start_period : int, optional
        Starting period number (default: 1)
    end_period : int, optional
        Ending period number (default: None, uses maximum available)

    Returns:
    pd.DataFrame
        Combined and summed forecast data across all periods
    """
    if end_period is None:
        max_periods = forecast_data.shape[0] // num_magnitude_steps
        end_period = max_periods

    print(f"Generating forecast data for periods {start_period} to {end_period}...")

    all_periods_data = []

    for period in range(start_period, end_period + 1):
        print(f"Processing period {period} of {end_period}...")
        try:
            period_forecast = extract_period_forecast(period, forecast_data, num_magnitude_steps, magnitude_bins, num_regions, cell_bounds)
            # Call the new spatial downscaling function
            period_subgrid = create_subgrids_spatial(period_forecast)
            all_periods_data.append(period_subgrid)
        except Exception as e:
            print(f"Error occurred while processing period {period}: {str(e)}")

    if not all_periods_data:
        return pd.DataFrame()

    combined_data = pd.concat(all_periods_data, ignore_index=True)

    print("Summing forecast rates across periods...")

    # Round before grouping to avoid floating point precision issues
    combined_data['LON_0'] = combined_data['LON_0'].round(2)
    combined_data['LAT_0'] = combined_data['LAT_0'].round(2)

    # Group by 0.1° grid starting point and magnitude
    group_cols_simple = ['LON_0', 'LAT_0', 'MAG_0']

    # Define aggregation functions
    agg_funcs = {
        'RATE': 'sum', # Sum forecast rates
        'LON_1': 'first', # Take first value for other columns
        'LAT_1': 'first',
        'Z_0': 'first',
        'Z_1': 'first',
        'MAG_1': 'first',
        'FLAG': 'first'
    }

    summed_data = combined_data.groupby(group_cols_simple, as_index=False).agg(agg_funcs)

    print(f"Original data points: {len(combined_data)}, Summed data points: {len(summed_data)}")
    return summed_data

# Create CSEP-compatible output file
def create_csep_forecast_file(data, output_file):
    """
    Create CSEP-compatible forecast file.

    Args:
        data: Forecast data to write (pd.DataFrame)
        output_file: Path to output file (str)

    Returns:
    None
        Writes data to file in CSEP format
    """
    df = data.copy()

    # Ensure correct numeric format
    df['LON_0'] = df['LON_0'].astype(float)
    df['LON_1'] = df['LON_1'].astype(float)
    df['LAT_0'] = df['LAT_0'].astype(float)
    df['LAT_1'] = df['LAT_1'].astype(float)
    df['Z_0'] = df['Z_0'].astype(float)
    df['Z_1'] = df['Z_1'].astype(float)
    df['MAG_0'] = df['MAG_0'].astype(float)
    df['MAG_1'] = df['MAG_1'].astype(float)
    df['RATE'] = df['RATE'].astype(float)
    df['FLAG'] = df['FLAG'].astype(int)

    order = ['LON_0', 'LON_1', 'LAT_0', 'LAT_1', 'Z_0', 'Z_1', 'MAG_0', 'MAG_1', 'RATE', 'FLAG']

    with open(output_file, 'w') as f:
        for _, row in df[order].iterrows():
            line = f"{row['LON_0']}\t{row['LON_1']}\t{row['LAT_0']}\t{row['LAT_1']}\t{row['Z_0']}\t{row['Z_1']}\t{row['MAG_0']}\t{row['MAG_1']}\t{row['RATE']:.16e}\t{row['FLAG']}\n"
            f.write(line)

    print(f"Created CSEP-compatible file: {output_file}")


# Calculate date range
def calculate_date_range(start_year, period):
    """
    Calculate start and end dates based on starting year and period number.

    Args:
        start_year: Starting year of forecast (int)
        period: Period number (starting from 1) (int)

    Returns:
    tuple
        (start_date, end_date) representing the 3-month period
    """
    # Calculate quarter start
    quarter = ((period - 1) % 4) + 1  # Convert period to quarter (1-4)
    year_offset = (period - 1) // 4   # Calculate year offset
    year = start_year + year_offset

    # Set month based on quarter
    month = (quarter - 1) * 3 + 1

    # Create start date
    start_date = time_utils.strptime_to_utc_datetime(f'{year}-{month:02d}-01 00:00:00.0')

    # Calculate end date (last day of the three months)
    if month == 1:  # Quarter starting in January
        end_date = time_utils.strptime_to_utc_datetime(f'{year}-03-31 23:59:59.0')
    elif month == 4:  # Quarter starting in April
        end_date = time_utils.strptime_to_utc_datetime(f'{year}-06-30 23:59:59.0')
    elif month == 7:  # Quarter starting in July
        end_date = time_utils.strptime_to_utc_datetime(f'{year}-09-30 23:59:59.0')
    else:  # Quarter starting in October
        end_date = time_utils.strptime_to_utc_datetime(f'{year}-12-31 23:59:59.0')

    return start_date, end_date

def get_top_earthquakes(catalog_file, start_date, end_date, n=3):
    """
    Find the largest n earthquakes within the specified time range from earthquake catalog.

    *** WARNING: ***
    The provided logs show "Found 0 earthquakes". This most likely means that
    the hard-coded field indices (e.g., quake[6], quake[7], quake[9]) in this function
    do not match the actual format of your 'HORUS_Italy_filtered.mat' file.
    You must manually modify these indices (e.g., quake[i]) to correctly read earthquakes.

    Args:
        catalog_file: Path to earthquake catalog .mat file (str)
        start_date: Start of time range (datetime or str)
        end_date: End of time range (datetime or str)
    n : int, optional
        Number of top earthquakes to return (default: 3)

    Returns:
    list
        List of tuples (lon, lat, magnitude, time, depth) for top earthquakes
    """
    print(f"Reading earthquake catalog: {catalog_file}")

    if not os.path.exists(catalog_file):
        print(f"*** ERROR: Cannot find earthquake catalog file {catalog_file}. Skipping earthquake marking. ***")
        return []

    try:
        mat_data = scipy.io.loadmat(catalog_file)
        print(f"MATLAB file variable names: {list(mat_data.keys())}")

        catalog_key = None
        # Your logs show 'HORUS' is the correct key
        if 'HORUS' in mat_data:
            catalog_key = 'HORUS'
        else:
            data_vars = [k for k in mat_data.keys() if not k.startswith('__') and isinstance(mat_data[k], np.ndarray)]
            if data_vars:
                data_vars.sort(key=lambda k: mat_data[k].size, reverse=True)
                catalog_key = data_vars[0]
                print(f"Warning: 'HORUS' not found. Auto-using largest array: '{catalog_key}'")
            else:
                print("ERROR: Cannot find any earthquake catalog data array.")
                return []

        catalog = mat_data[catalog_key]
        print(f"Using variable '{catalog_key}' (Dimensions: {catalog.shape})")

        if isinstance(start_date, str):
            start_date = time_utils.strptime_to_utc_datetime(start_date)
        if isinstance(end_date, str):
            end_date = time_utils.strptime_to_utc_datetime(end_date)

        filtered_quakes = []

        # --- !!! You likely need to modify the indices here !!! ---
        # Assumed format: [0:Y, 1:M, 2:D, 3:H, 4:Min, 5:Sec, 6:Lat, 7:Lon, 8:Depth, 9:Mag]
        print("Iterating through catalog (assuming format: Y,M,D,H,M,S,Lat,Lon,Depth,Mag)...")
        print("...If format differs, please modify the quake[i] indices in this function.")
        for quake in catalog:
            try:
                year, month, day = int(quake[0]), int(quake[1]), int(quake[2])
                hour, minute = int(quake[3]), int(quake[4])
                second = float(quake[5])
                lat, lon = float(quake[6]), float(quake[7]) # Latitude in column 7, longitude in column 8
                depth, magnitude = float(quake[8]), float(quake[9])

                second_int = int(second)
                microsecond = int((second - second_int) * 1000000)

                quake_time = datetime(
                    year, month, day,
                    hour, minute, second_int,
                    microsecond=microsecond,
                    tzinfo=timezone.utc
                )

                if start_date <= quake_time <= end_date:
                    filtered_quakes.append((lon, lat, magnitude, quake_time, depth))
            except (ValueError, IndexError) as e:
                pass # Skip invalid dates or data that doesn't match format

        print(f"Found {len(filtered_quakes)} earthquakes within the specified time range")
        top_earthquakes = sorted(filtered_quakes, key=lambda x: x[2], reverse=True)[:n]

        print(f"Top {len(top_earthquakes)} earthquakes:")
        for i, eq in enumerate(top_earthquakes):
            print(f"  {i+1}. Magnitude {eq[2]:.1f}, Location: ({eq[0]:.4f}°E, {eq[1]:.4f}°N), Depth: {eq[4]:.1f}km")

        return top_earthquakes

    except Exception as e:
        print(f"Serious error occurred while reading earthquake catalog: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def my_custom_loader_function(filename):
    """
    Custom loader function for HORUS_TW_A.mat catalog data.

    Args:
        filename: Path to the .mat file containing the earthquake catalog (str)

    Returns:
    eventlist: list
        List of events compatible with PyCSEP, each event as a tuple:
        (event_id, origin_time, latitude, longitude, depth, magnitude)
    """
    # Load the .mat file
    try:
        mat_data = scipy.io.loadmat(filename)
        # Try to find the HORUS data
        if 'HORUS' in mat_data:
            horus_data = mat_data['HORUS']
        else:
            # Find the largest array in the .mat file as a fallback
            largest_var = None
            largest_size = 0
            for key, value in mat_data.items():
                if isinstance(value, np.ndarray) and value.size > largest_size:
                    if not key.startswith('__'):  # Skip metadata variables
                        largest_var = key
                        largest_size = value.size

            if largest_var is None:
                raise ValueError(f"No suitable data array found in {filename}")

            horus_data = mat_data[largest_var]
    except Exception as e:
        raise IOError(f"Failed to load {filename}: {str(e)}")

    # Process each earthquake event
    eventlist = []
    skipped = 0
    for i, event in enumerate(horus_data):
        try:
            # Extract data from columns according to the provided format
            year = int(event[0])
            month = int(event[1])
            day = int(event[2])
            hour = int(event[3])
            minute = int(event[4])

            # Properly handle floating-point seconds
            second_float = float(event[5])
            second = int(second_float)
            microsecond = int((second_float - second) * 1000000)

            latitude = float(event[6])
            longitude = float(event[7])
            depth = float(event[8])
            magnitude = round(float(event[9]), 1)  # Round magnitude to one decimal place

            # Create datetime object with proper microsecond handling
            try:
                dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
                # Convert to PyCSEP compatible format (float timestamp)
                origin_time = time_utils.datetime_to_utc_epoch(dt)
            except (ValueError, OverflowError) as e:
                # Skip events with invalid dates
                if skipped < 10:  # Only show first 10 errors to avoid excessive output
                    print(f"Skipping event {i}: Invalid datetime ({year}-{month}-{day} {hour}:{minute}:{second_float}) - {e}")
                elif skipped == 10:
                    print("More invalid events found. Suppressing further messages...")
                skipped += 1
                continue

            # Generate a unique event ID (string)
            event_id = f'HORUS-{i+1:06d}'

            # Add the event to the list with proper types
            eventlist.append((event_id, origin_time, latitude, longitude, depth, magnitude))

        except (ValueError, IndexError) as e:
            if skipped < 10:
                print(f"Skipping event {i}: {e}")
            elif skipped == 10:
                print("More errors found. Suppressing further messages...")
            skipped += 1
            continue

    print(f"Successfully loaded {len(eventlist)} events from {filename}")
    if skipped > 0:
        print(f"Note: {skipped} events were skipped due to errors")
    return eventlist
