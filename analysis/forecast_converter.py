#!/usr/bin/env python3
"""
EEPAS Forecast to PyCSEP Converter

Complete forecast format conversion tool supporting:
- EEPAS/PPE forecast MATLAB format → PyCSEP GriddedForecast
- Coordinate transformation (RDN2008 → WGS84)
- Spatial downsampling (coarse grids → 0.1° sub-grids)
- Time period handling (3-month/1-year periods)

Author: EEPAS Team
Date: 2025-11-26
Version: 1.0.0
"""

import numpy as np
import pandas as pd
import scipy.io as sio
from datetime import datetime, timedelta
from tqdm import tqdm
import os

try:
    from pyproj import Transformer
except ImportError:
    Transformer = None
    print("Warning: pyproj not installed. Coordinate transformation will not work.")

try:
    import csep
    from csep.utils import time_utils
except ImportError:
    csep = None
    print("Warning: pycsep not installed. PyCSEP format export will not work.")


class EEPASForecastConverter:
    """
    EEPAS Forecast Format Converter

    Features:

        1. Load EEPAS/PPE MATLAB forecast files
        2. Load grid definitions (CELLE_ter.mat) and perform coordinate transformation
        3. Extract forecasts for specific time periods
        4. Spatial downsampling (coarse grids → 0.1° sub-grids)
        5. Export PyCSEP-compatible format

    Examples:
        >>> # Basic usage
        >>> converter = EEPASForecastConverter(
        ...     forecast_file='PREVISIONI_3m_EEPAS_2012_2022.mat',
        ...     grid_file='CELLE_ter.mat'
        ... )
        >>>
        >>> # Convert specific period
        >>> converter.convert_period(
        ...     period=1,
        ...     start_year=2012,
        ...     output_file='forecast_period_1.dat'
        ... )
        >>>
        >>> # Convert all periods (sum rates)
        >>> converter.convert_all_periods(
        ...     start_year=2012,
        ...     output_file='forecast_all_periods.dat'
        ... )
    """
    
    def __init__(self, forecast_file, grid_file,
                 num_regions=177, num_magnitude_steps=25,
                 magnitude_min=5.0, magnitude_step=0.1,
                 depth_min=0.0, depth_max=30.0,
                 coordinate_transform=True,
                 source_crs='EPSG:7794', target_crs='EPSG:4326',
                 verbose=True):
        """
        Initialize converter
        
        Args:
            forecast_file: Path to EEPAS/PPE forecast .mat file
            grid_file: Path to grid definition .mat file (CELLE_ter.mat)
            num_regions: Number of spatial grids (default: 177 for Italy)
            num_magnitude_steps: Number of magnitude bins (default: 25)
            magnitude_min: Minimum magnitude (default: 5.0)
            magnitude_step: Magnitude bin width (default: 0.1)
            depth_min: Minimum depth in km (default: 0.0)
            depth_max: Maximum depth in km (default: 30.0)
            coordinate_transform: Enable coordinate transformation (default: True)
            source_crs: Source coordinate system (default: 'EPSG:7794' for RDN2008)
            target_crs: Target coordinate system (default: 'EPSG:4326' for WGS84)
            verbose: Print verbose messages (default: True)
        """
        self.forecast_file = forecast_file
        self.grid_file = grid_file
        self.num_regions = num_regions
        self.num_magnitude_steps = num_magnitude_steps
        self.magnitude_min = magnitude_min
        self.magnitude_step = magnitude_step
        self.depth_min = depth_min
        self.depth_max = depth_max
        self.coordinate_transform = coordinate_transform
        self.source_crs = source_crs
        self.target_crs = target_crs
        self.verbose = verbose
        
        # Load data
        self._load_forecast()
        self._load_grid()
        self._create_magnitude_bins()
    
    def _log(self, message):
        """Internal logging function"""
        if self.verbose:
            print(message)
    
    def _load_forecast(self):
        """
        Load forecast data from MATLAB file.

        Auto-detects variable name in .mat file:
            - 'forecast_eepas': EEPAS forecast matrix (preferred naming)
            - 'PREVISIONI_3m_less': Legacy Italian naming for EEPAS forecast
            - 'PREVISIONI_3m': PPE forecast matrix
            - First non-metadata variable if none of above found

        Returns:
            None: Sets self.forecast_data and self.num_periods
        """
        self._log(f"Loading forecast file: {self.forecast_file}")

        mat_data = sio.loadmat(self.forecast_file)

        # Auto-detect variable name (priority order)
        if 'forecast_eepas' in mat_data:
            key = 'forecast_eepas'
        elif 'PREVISIONI_3m_less' in mat_data:
            key = 'PREVISIONI_3m_less'  # Legacy Italian naming
        elif 'PREVISIONI_3m' in mat_data:
            key = 'PREVISIONI_3m'
        else:
            # Find largest non-metadata array
            potential_keys = [k for k in mat_data.keys() if not k.startswith('__')]
            if not potential_keys:
                raise ValueError("Cannot find forecast data variable")
            key = potential_keys[0]

        self.forecast_data = mat_data[key]
        self._log(f"   Variable name: {key}")
        self._log(f"   Data shape: {self.forecast_data.shape}")

        # Calculate number of periods
        self.num_periods = self.forecast_data.shape[0] // self.num_magnitude_steps
        self._log(f"   Detected {self.num_periods} time periods")
    
    def _load_grid(self):
        """
        Load and transform grid definitions from MATLAB file.

        Reads CELLESD variable containing grid boundaries and optionally
        transforms coordinates from source CRS (e.g., RDN2008) to target CRS (e.g., WGS84).

        Returns:
            None: Sets self.cell_bounds DataFrame
        """
        self._log(f"\nLoading grid definition: {self.grid_file}")
        
        mat_data = sio.loadmat(self.grid_file)
        
        # Find grid data
        if 'CELLESD' in mat_data:
            cells_data = mat_data['CELLESD'][:, :4]  # First 4 columns (x_min, x_max, y_min, y_max)
        else:
            raise ValueError("Cannot find 'CELLESD' variable")
        
        if self.coordinate_transform:
            self._log("   Performing coordinate transformation...")
            if Transformer is None:
                raise ImportError("pyproj required for coordinate transformation: pip install pyproj")
            
            # Convert to meters (if in kilometers)
            data_m = cells_data * 1000
            
            # Create transformer
            transformer = Transformer.from_crs(
                self.source_crs,
                self.target_crs,
                always_xy=True
            )
            
            cells_lonlat = []
            for i in tqdm(range(len(data_m)), desc="   Converting grids", disable=not self.verbose):
                x_min, x_max, y_min, y_max = data_m[i]
                
                # Transform four corners
                corners_xy = [
                    (x_min, y_min), (x_max, y_min),
                    (x_min, y_max), (x_max, y_max)
                ]
                
                lons, lats = transformer.transform(
                    [p[0] for p in corners_xy],
                    [p[1] for p in corners_xy]
                )
                
                # Create bounding box
                cells_lonlat.append({
                    'LON_0': np.min(lons),
                    'LON_1': np.max(lons),
                    'LAT_0': np.min(lats),
                    'LAT_1': np.max(lats)
                })
            
            self.cell_bounds = pd.DataFrame(cells_lonlat)
        else:
            # Use directly (assuming already in lat/lon)
            self.cell_bounds = pd.DataFrame(
                cells_data,
                columns=['LON_0', 'LON_1', 'LAT_0', 'LAT_1']
            )
        
        self._log(f"   Successfully loaded {len(self.cell_bounds)} grids")
    
    def _create_magnitude_bins(self):
        """
        Create magnitude bins for forecast matrix.

        Generates list of (mag_min, mag_max) tuples based on magnitude_min,
        magnitude_step, and num_magnitude_steps.

        Returns:
            None: Sets self.magnitude_bins list
        """
        self.magnitude_bins = []
        for i in range(self.num_magnitude_steps):
            mag_0 = self.magnitude_min + self.magnitude_step * i
            mag_1 = mag_0 + self.magnitude_step
            self.magnitude_bins.append((round(mag_0, 2), round(mag_1, 2)))
        
        self._log(f"\nMagnitude range: M{self.magnitude_min} - M{self.magnitude_bins[-1][1]}")
        self._log(f"   Total {len(self.magnitude_bins)} magnitude bins")
    
    def extract_period(self, period_idx):
        """
        Extract forecast data for specific period
        
        Args:
            period_idx: Period index (starting from 1)
        
        Returns:
            pd.DataFrame: Coarse-grid forecast data for the period
        """
        if period_idx < 1 or period_idx > self.num_periods:
            raise ValueError(f"Period index out of range: {period_idx} (valid: 1-{self.num_periods})")
        
        start_idx = (period_idx - 1) * self.num_magnitude_steps
        end_idx = start_idx + self.num_magnitude_steps
        
        period_rows = self.forecast_data[start_idx:end_idx]
        
        rows = []
        for mag_idx in range(min(len(period_rows), self.num_magnitude_steps)):
            mag_0, mag_1 = self.magnitude_bins[mag_idx]
            mag_row = period_rows[mag_idx]
            period_number = int(mag_row[0])
            
            for region_idx in range(min(self.num_regions, len(self.cell_bounds))):
                rate = float(mag_row[region_idx + 1])  # +1 because column 0 is period number
                region = self.cell_bounds.iloc[region_idx]
                
                rows.append({
                    'LON_0': float(region['LON_0']),
                    'LON_1': float(region['LON_1']),
                    'LAT_0': float(region['LAT_0']),
                    'LAT_1': float(region['LAT_1']),
                    'Z_0': self.depth_min,
                    'Z_1': self.depth_max,
                    'MAG_0': mag_0,
                    'MAG_1': mag_1,
                    'RATE': rate,
                    'FLAG': 1,
                    'PERIOD': period_number
                })
        
        return pd.DataFrame(rows)
    
    def spatial_downsampling(self, data, grid_resolution=0.1):
        """
        Spatial downsampling: divide coarse grids into 0.1° × 0.1° sub-grids
        
        Uses "centroid-in-bounding-box" method for spatial downsampling
        
        Args:
            data: Coarse-grid forecast data (pd.DataFrame)
            grid_resolution: Sub-grid resolution in degrees (default: 0.1)
        
        Returns:
            pd.DataFrame: Downsampled forecast data
        """
        self._log(f"\nPerforming spatial downsampling (→ {grid_resolution}° × {grid_resolution}°)")
        
        new_rows = []
        
        for _, row in tqdm(data.iterrows(), total=len(data),
                          desc="   Processing sub-grids", disable=not self.verbose):
            # Get coarse grid bounding box
            coarse_lon_0 = row['LON_0']
            coarse_lon_1 = row['LON_1']
            coarse_lat_0 = row['LAT_0']
            coarse_lat_1 = row['LAT_1']
            coarse_rate = row['RATE']
            
            mag_0 = row['MAG_0']
            mag_1 = row['MAG_1']
            period = row.get('PERIOD', 1)
            
            # Find 0.1° grid range that completely covers this bounding box
            sub_lon_start = np.floor(coarse_lon_0 * 10) / 10
            sub_lon_end = np.ceil(coarse_lon_1 * 10) / 10
            sub_lat_start = np.floor(coarse_lat_0 * 10) / 10
            sub_lat_end = np.ceil(coarse_lat_1 * 10) / 10
            
            # Generate candidate sub-grid starting points
            sub_lons = np.arange(sub_lon_start, sub_lon_end, grid_resolution)
            sub_lats = np.arange(sub_lat_start, sub_lat_end, grid_resolution)
            
            # Find all sub-grids whose centroids fall within coarse grid bounds
            sub_cells_in_coarse = []
            for lon_0 in sub_lons:
                for lat_0 in sub_lats:
                    # Calculate sub-grid centroid
                    lon_center = lon_0 + (grid_resolution / 2)
                    lat_center = lat_0 + (grid_resolution / 2)
                    
                    # Check if centroid is within coarse grid
                    if (coarse_lon_0 <= lon_center < coarse_lon_1) and \
                       (coarse_lat_0 <= lat_center < coarse_lat_1):
                        sub_cells_in_coarse.append((lon_0, lat_0))
            
            num_subcells = len(sub_cells_in_coarse)
            
            # Evenly distribute RATE
            subcell_rate = coarse_rate / num_subcells if num_subcells > 0 else 0
            
            if num_subcells == 0:
                # Coarse grid too small, no sub-grid centroids fall inside
                continue
            
            # Add row for each valid sub-grid
            for lon_0, lat_0 in sub_cells_in_coarse:
                new_rows.append({
                    'LON_0': round(lon_0, 2),
                    'LON_1': round(lon_0 + grid_resolution, 2),
                    'LAT_0': round(lat_0, 2),
                    'LAT_1': round(lat_0 + grid_resolution, 2),
                    'Z_0': self.depth_min,
                    'Z_1': self.depth_max,
                    'MAG_0': mag_0,
                    'MAG_1': mag_1,
                    'RATE': subcell_rate,
                    'FLAG': 1,
                    'PERIOD': period
                })
        
        result = pd.DataFrame(new_rows)
        self._log(f"   Original: {len(data)} coarse grids → Downsampled: {len(result)} 0.1° grids")
        
        return result
    
    def aggregate_overlaps(self, data):
        """
        Aggregate overlapping grid points (duplicates from bounding box overlaps)
        
        Args:
            data: Downsampled data (pd.DataFrame)
        
        Returns:
            pd.DataFrame: Aggregated data
        """
        self._log("\nAggregating overlapping grid points...")
        
        # Round to avoid floating-point precision issues
        data_copy = data.copy()
        data_copy['LON_0'] = data_copy['LON_0'].round(2)
        data_copy['LAT_0'] = data_copy['LAT_0'].round(2)
        
        # Group by 0.1° grid starting point and magnitude
        group_cols = ['LON_0', 'LAT_0', 'MAG_0']
        
        agg_funcs = {
            'RATE': 'sum',       # Sum forecast rates
            'LON_1': 'first',
            'LAT_1': 'first',
            'Z_0': 'first',
            'Z_1': 'first',
            'MAG_1': 'first',
            'FLAG': 'first',
            'PERIOD': 'first'
        }
        
        aggregated = data_copy.groupby(group_cols, as_index=False).agg(agg_funcs)
        
        self._log(f"   Original: {len(data)} grid points → Aggregated: {len(aggregated)} unique points")
        
        return aggregated
    
    def convert_period(self, period, start_year=None, output_file=None,
                      perform_downsampling=True, grid_resolution=0.1):
        """
        Convert specific period to PyCSEP format
        
        Args:
            period: Period number (starting from 1)
            start_year: Forecast start year (for time range calculation, optional)
            output_file: Output file path (optional)
            perform_downsampling: Enable spatial downsampling (default: True)
            grid_resolution: Downsampling resolution in degrees (default: 0.1)
        
        Returns:
            pd.DataFrame: PyCSEP-format forecast data
        """
        self._log(f"\n{'='*70}")
        self._log(f"Converting Period {period}")
        self._log(f"{'='*70}")
        
        # 1. Extract period data
        period_data = self.extract_period(period)
        self._log(f"Extracted: {len(period_data)} coarse grid-magnitude bins")
        
        # 2. Spatial downsampling (optional)
        if perform_downsampling:
            downsampled = self.spatial_downsampling(period_data, grid_resolution)
            final_data = self.aggregate_overlaps(downsampled)
        else:
            final_data = period_data
        
        # 3. Sort
        final_data = final_data.sort_values(
            by=['LON_0', 'LAT_0', 'MAG_0']
        ).reset_index(drop=True)
        
        # 4. Export file (optional)
        if output_file:
            self.export_csep_format(final_data, output_file)
        
        self._log(f"\nPeriod {period} conversion complete!")
        self._log(f"   Final grid points: {len(final_data)}")
        
        return final_data
    
    def convert_all_periods(self, start_period=1, end_period=None,
                           start_year=None, output_file=None,
                           perform_downsampling=True, grid_resolution=0.1):
        """
        Convert all periods and sum RATE
        
        Args:
            start_period: Starting period (from 1)
            end_period: Ending period (None = all)
            start_year: Forecast start year (optional)
            output_file: Output file path (optional)
            perform_downsampling: Enable spatial downsampling
            grid_resolution: Downsampling resolution in degrees
        
        Returns:
            pd.DataFrame: Summed forecast data for all periods
        """
        if end_period is None:
            end_period = self.num_periods
        
        self._log(f"\n{'='*70}")
        self._log(f"Converting All Periods ({start_period} - {end_period})")
        self._log(f"{'='*70}")
        
        all_periods_data = []
        
        for period in range(start_period, end_period + 1):
            self._log(f"\nProcessing period {period}/{end_period}...")
            
            # Extract and downsample
            period_data = self.extract_period(period)
            
            if perform_downsampling:
                downsampled = self.spatial_downsampling(period_data, grid_resolution)
                all_periods_data.append(downsampled)
            else:
                all_periods_data.append(period_data)
        
        # Combine all periods
        self._log("\nCombining all periods...")
        combined_data = pd.concat(all_periods_data, ignore_index=True)
        
        # Aggregate: sum RATE by grid and magnitude
        self._log("\nSumming forecast rates across periods...")
        combined_data['LON_0'] = combined_data['LON_0'].round(2)
        combined_data['LAT_0'] = combined_data['LAT_0'].round(2)
        
        group_cols = ['LON_0', 'LAT_0', 'MAG_0']
        agg_funcs = {
            'RATE': 'sum',
            'LON_1': 'first',
            'LAT_1': 'first',
            'Z_0': 'first',
            'Z_1': 'first',
            'MAG_1': 'first',
            'FLAG': 'first'
        }
        
        summed_data = combined_data.groupby(group_cols, as_index=False).agg(agg_funcs)
        
        # Sort
        summed_data = summed_data.sort_values(
            by=['LON_0', 'LAT_0', 'MAG_0']
        ).reset_index(drop=True)
        
        self._log(f"\n   Before merge: {len(combined_data)} grid points")
        self._log(f"   After summing: {len(summed_data)} unique grid points")
        
        # Export file (optional)
        if output_file:
            self.export_csep_format(summed_data, output_file)
        
        self._log(f"\nAll periods conversion complete!")
        
        return summed_data
    
    def export_csep_format(self, data, output_file):
        """
        Export PyCSEP-compatible format
        
        Format: LON_0 LON_1 LAT_0 LAT_1 Z_0 Z_1 MAG_0 MAG_1 RATE FLAG
        
        Args:
            data: Forecast data (pd.DataFrame)
            output_file: Output file path
        """
        self._log(f"\nExporting PyCSEP format: {output_file}")
        
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
        
        order = ['LON_0', 'LON_1', 'LAT_0', 'LAT_1', 'Z_0', 'Z_1',
                 'MAG_0', 'MAG_1', 'RATE', 'FLAG']
        
        with open(output_file, 'w') as f:
            for _, row in df[order].iterrows():
                line = (f"{row['LON_0']}\t{row['LON_1']}\t"
                       f"{row['LAT_0']}\t{row['LAT_1']}\t"
                       f"{row['Z_0']}\t{row['Z_1']}\t"
                       f"{row['MAG_0']}\t{row['MAG_1']}\t"
                       f"{row['RATE']:.16e}\t{row['FLAG']}\n")
                f.write(line)
        
        self._log(f"   Successfully exported {len(df)} rows")
    
    def to_pycsep_forecast(self, data, start_date, end_date, name='EEPAS_Forecast'):
        """
        Convert to PyCSEP GriddedForecast object
        
        Args:
            data: Forecast data (pd.DataFrame)
            start_date: Forecast start time (datetime or str)
            end_date: Forecast end time (datetime or str)
            name: Forecast name (str)
        
        Returns:
            csep.core.forecasts.GriddedForecast: PyCSEP forecast object
        
        Examples:
            >>> from datetime import datetime
            >>> forecast = converter.to_pycsep_forecast(
            ...     data=period_data,
            ...     start_date=datetime(2012, 1, 1),
            ...     end_date=datetime(2012, 3, 31),
            ...     name='EEPAS_2012_Q1'
            ... )
        """
        if csep is None:
            raise ImportError("pycsep required: pip install pycsep")
        
        # Export to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as tmp:
            tmp_file = tmp.name
            self.export_csep_format(data, tmp_file)
        
        try:
            # Handle time
            if isinstance(start_date, str):
                start_date = time_utils.strptime_to_utc_datetime(start_date)
            if isinstance(end_date, str):
                end_date = time_utils.strptime_to_utc_datetime(end_date)
            
            # Load as PyCSEP forecast
            forecast = csep.load_gridded_forecast(
                tmp_file,
                start_date=start_date,
                end_date=end_date,
                name=name
            )
            
            return forecast
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
    
    def calculate_period_dates(self, period, start_year, period_length_months=3):
        """
        Calculate start and end dates for specific period
        
        Args:
            period: Period number (starting from 1)
            start_year: Forecast start year
            period_length_months: Months per period (default: 3)
        
        Returns:
            tuple: (start_date, end_date) as datetime objects
        
        Examples:
            >>> # 3-month periods
            >>> start, end = converter.calculate_period_dates(1, 2012, 3)
            >>> # 1-year periods
            >>> start, end = converter.calculate_period_dates(1, 2012, 12)
        """
        from dateutil.relativedelta import relativedelta
        
        # Calculate starting month
        months_offset = (period - 1) * period_length_months
        start_date = datetime(start_year, 1, 1) + relativedelta(months=months_offset)
        
        # Calculate end date
        end_date = start_date + relativedelta(months=period_length_months)
        
        return start_date, end_date


# ========== Convenience Functions ==========

def convert_eepas_forecast(forecast_file, grid_file, output_file,
                          period=None, **kwargs):
    """
    Convenience function: quick EEPAS forecast conversion.

    Args:
        forecast_file (str): EEPAS forecast .mat file path
        grid_file (str): Grid definition .mat file path
        output_file (str): Output PyCSEP format file path
        period (int, optional): Period number (None = all periods)
        **kwargs: Additional parameters for EEPASForecastConverter

    Returns:
        None: Writes PyCSEP format file to output_file

    Examples:
        >>> # Convert specific period
        >>> convert_eepas_forecast(
        ...     'PREVISIONI_3m_EEPAS_2012_2022.mat',
        ...     'CELLE_ter.mat',
        ...     'forecast_period_1.dat',
        ...     period=1
        ... )
        >>>
        >>> # Convert all periods
        >>> convert_eepas_forecast(
        ...     'PREVISIONI_3m_EEPAS_2012_2022.mat',
        ...     'CELLE_ter.mat',
        ...     'forecast_all_periods.dat'
        ... )
    """
    converter = EEPASForecastConverter(forecast_file, grid_file, **kwargs)
    
    if period is not None:
        converter.convert_period(period, output_file=output_file)
    else:
        converter.convert_all_periods(output_file=output_file)
    
    print(f"\nConversion complete: {output_file}")


if __name__ == '__main__':
    # Simple test example
    print("EEPAS Forecast Converter - Test Mode")
    print("Please use test_forecast_converter.py for complete testing")
