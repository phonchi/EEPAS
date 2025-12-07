import numpy as np
import pandas as pd
import scipy.io
import os

def select_events_with_options(
    catalog_file,
    output_file,
    min_mag=6.0,
    start_year=1988,
    end_year=2025,
    max_depth=40.0,
    MC=2.5,
    exclude_921_aftershocks=True
):
    """
    Select earthquakes from the catalog based on specified criteria, with optional exclusion of 921 earthquake aftershocks.

    Args:
        catalog_file (str): Input .mat file name.
        output_file (str): Output file name.
        min_mag (float): Minimum magnitude to filter.
        start_year (int): Starting year to filter (inclusive).
        end_year (int): Ending year to filter (exclusive).
        max_depth (float): Maximum depth to filter (exclusive), in kilometers.
        MC (float): A custom parameter, default is 2.5.
        exclude_921_aftershocks (bool): Whether to exclude 921 aftershocks, default is True.
    """
    if not os.path.exists(catalog_file):
        print(f"Error: File '{catalog_file}' not found. Please confirm the file has been uploaded.")
        return

    try:
        mat_data = scipy.io.loadmat(catalog_file)
        var_name = [k for k in mat_data if not k.startswith('__')][0]
        cat = mat_data[var_name]
        print(f"Successfully loaded variable '{var_name}' from '{catalog_file}'.")
    except Exception as e:
        print(f"Failed to read file '{catalog_file}': {e}")
        return

    columns = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Latitude', 'Longitude', 'Depth', 'Magnitude']
    df = pd.DataFrame(cat, columns=columns)

    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']].astype(int), errors='coerce')
    df.dropna(subset=['datetime'], inplace=True)

    # --- Define filter conditions ---
    # 1. Basic conditions: magnitude, year and depth
    final_mask = (
        (df['Magnitude'] >= min_mag) &
        (df['Year'] >= start_year) &
        (df['Year'] < end_year) &
        (df['Depth'] < max_depth)
    )

    # 2. Decide whether to add exclusion condition based on option
    if exclude_921_aftershocks:
        print("921 aftershock exclusion enabled.")
        aftershock_exclusion_condition = ~(
            (df['datetime'] >= '1999-09-21') &
            (df['datetime'] <= '1999-12-31')
        )
        final_mask = final_mask & aftershock_exclusion_condition
    else:
        print("921 aftershock exclusion disabled.")

    # 3. Apply final filter conditions
    selected_df = df[final_mask].copy()
    n = len(selected_df)

    if n == 0:
        print(f"No earthquakes found matching criteria (M>={min_mag}, year between {start_year} and {end_year}, depth < {max_depth}km).")
        return

    # --- Post-processing and write to file ---
    names = [f"K7EQ{i}" for i in range(1, n + 1)]
    selected_df['name'] = names
    selected_df['startyr'] = selected_df['Year'] - 30
    selected_df['endyr'] = selected_df['Year'] + 1
    cati = "K7"

    with open(output_file, 'w') as f:
        for _, row in selected_df.iterrows():
            lineout = [
                row['name'], cati,
                int(row['startyr']), 1, 1,
                int(row['Year']), int(row['Month']), int(row['Day']),
                int(row['endyr']), 1, 1,
                row['Latitude'], row['Longitude'], MC,
                int(row['Hour']), 0, 0, row['Magnitude']
            ]
            line_str = ' '.join(map(str, lineout))
            f.write(line_str + '\n')

    exclusion_status = "921 aftershocks excluded" if exclude_921_aftershocks else "921 aftershocks not excluded"

    print(f"Selected {n} M{min_mag}+ earthquakes (year >= {start_year} and < {end_year}, depth < {max_depth}km, {exclusion_status}) and wrote to '{output_file}'")
