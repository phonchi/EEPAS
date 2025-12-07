"""
CatalogProcessor - Seismic Catalog Preprocessing Utility Class

Provides unified earthquake catalog quality control, time conversion, and filtering functions.

Format Support:
    This module uses HORUS format (10 columns) as the internal standard:
        year, month, day, hour, minute, second, lat, lon, depth, mag

    Extended format conversion support (via catalog_processor_extensions):
        - Input formats: ZMAP, CSEP, QuakeML, DataFrame, SeismoStats, pyCSEP, INGV HORUS
        - Output formats: MATLAB .mat, SeismoStats Catalog, pyCSEP CSEPCatalog
        - Methods: from_zmap(), from_csep(), from_quakeml(), from_dataframe(),
                  from_seismostats(), from_pycsep(), from_ingv_horus(),
                  to_mat(), to_seismostats(), to_pycsep()

    All conversion methods are available as static methods on CatalogProcessor class.
"""

import numpy as np
from datetime import datetime

# Import all conversion functions from extensions module
try:
    from . import catalog_processor_extensions as ext
    _EXTENSIONS_AVAILABLE = True
except ImportError:
    _EXTENSIONS_AVAILABLE = False


def decyear(date_array):
    """
    Convert date to decimal year.

    Args:
        date_array: Nx6 matrix [year, month, day, hour, minute, second]

    Returns:
        np.array: Decimal year
    """
    result = np.zeros(date_array.shape[0])

    for i in range(date_array.shape[0]):
        year = int(date_array[i, 0])
        month = int(date_array[i, 1])
        day = int(date_array[i, 2])
        hour = int(date_array[i, 3])
        minute = int(date_array[i, 4])
        second = float(date_array[i, 5])

        # Handle anomalous second values (some datasets may have second >= 60)
        # Convert seconds over 60 to minutes
        if second >= 60.0:
            extra_minutes = int(second / 60.0)
            minute += extra_minutes
            second = second - extra_minutes * 60.0

        # Handle anomalous minute values
        if minute >= 60:
            extra_hours = int(minute / 60)
            hour += extra_hours
            minute = minute - extra_hours * 60

        # Handle anomalous hour values
        if hour >= 24:
            extra_days = int(hour / 24)
            day += extra_days
            hour = hour - extra_days * 24

        # Calculate day of year (using total seconds method to handle month overflow)
        try:
            dt = datetime(year, month, day, hour, minute, int(second))
        except ValueError:
            # If date is still invalid (e.g. month overflow), use approximation
            # This is fault-tolerant handling to ensure program continues
            dt = datetime(year, 1, 1, 0, 0, 0)
            # Add total seconds
            total_seconds = ((month - 1) * 30 * 86400 + (day - 1) * 86400 +
                           hour * 3600 + minute * 60 + second)
            from datetime import timedelta
            dt = dt + timedelta(seconds=total_seconds)

        start_of_year = datetime(year, 1, 1)
        days_in_year = (datetime(year + 1, 1, 1) - start_of_year).days
        day_of_year = (dt - start_of_year).total_seconds() / 86400.0

        result[i] = year + day_of_year / days_in_year

    return result


class CatalogProcessor:
    """Seismic catalog preprocessing utility class"""

    @staticmethod
    def preprocess_catalog(HORUS, catalog_start_year, learn_start_year, learn_end_year,
                          completeness_threshold=2.0, max_depth=40, target_magnitude=None,
                          filter_target_mag=False, verbose=False):
        """
        General preprocessing pipeline for earthquake catalogs.
        Standardizes magnitudes, filters quality, converts time coordinates.

        Args:
            HORUS: Raw seismic catalog matrix
            catalog_start_year: Catalog start year
            learn_start_year: Learning start year
            learn_end_year: Learning end year
            completeness_threshold: Completeness magnitude threshold
            max_depth: Maximum depth (km)
            target_magnitude: PPE target magnitude
            filter_target_mag: Whether to enable target magnitude filtering
            verbose: Verbose output mode

        Returns:
            tuple: (HORUS_processed, T1, T2)
        """
        HORUS = HORUS.copy()  # Avoid modifying original data

        if verbose:
            print(f'Starting catalog preprocessing (initial size: {HORUS.shape[0]})...')

        # 1. Round earthquake magnitudes to first decimal place
        # MATLAB's round(x,1) rounds ties away from zero; numpy.round uses bankers rounding.
        mags = HORUS[:, 9]
        HORUS[:, 9] = np.sign(mags) * np.floor(np.abs(mags) * 10 + 0.5) / 10.0
        if verbose:
            print(f'After magnitude rounding: {HORUS.shape[0]} earthquakes')

        # 2. Filter depth events (remove earthquakes with depth > max_depth)
        # Note: MATLAB indexing starts from 1, Python from 0, so column indices subtract 1
        depth_filter = HORUS[:, 8] <= max_depth  # Column 9 is depth (index 8)
        HORUS = HORUS[depth_filter, :]
        if verbose:
            print(f'After depth filtering (depth<={max_depth}km): {HORUS.shape[0]} earthquakes')

        # 3. Filter events below completeness threshold
        mag_filter = HORUS[:, 9] >= completeness_threshold  # Column 10 is magnitude (index 9)
        HORUS = HORUS[mag_filter, :]
        if verbose:
            print(f'After completeness filtering (magnitude>={completeness_threshold}): {HORUS.shape[0]} earthquakes')

        # 4. Convert time to decimal year and relative days
        date_array = HORUS[:, 0:6]  # First 6 columns: year/month/day/hour/minute/second
        DECY = decyear(date_array)

        # If HORUS only has 10 columns, add column 11
        if HORUS.shape[1] == 10:
            HORUS = np.column_stack([HORUS, np.zeros(HORUS.shape[0])])

        HORUS[:, 10] = DECY  # Column 11 stores decimal year
        HORUS[:, 10] = (HORUS[:, 10] - catalog_start_year) * 365.2425  # Convert to relative days
        if verbose:
            print(f'Time conversion completed (relative to year {catalog_start_year})')

        # 5. Filter events outside time range
        time_filter = HORUS[:, 0] < learn_end_year  # Column 1 is year (index 0)
        HORUS = HORUS[time_filter, :]
        if verbose:
            print(f'After time range filtering ({catalog_start_year}~{learn_end_year}): {HORUS.shape[0]} earthquakes')

        # Calculate time conversion constants
        T1 = (learn_start_year - catalog_start_year) * 365.2425
        T2 = (learn_end_year - catalog_start_year) * 365.2425

        # 6. Optional: filter earthquakes below target magnitude
        if filter_target_mag and target_magnitude is not None:
            target_mag_filter = HORUS[:, 9] >= target_magnitude
            HORUS = HORUS[target_mag_filter, :]
            if verbose:
                print(f'After target magnitude filtering (magnitude>={target_magnitude}): {HORUS.shape[0]} earthquakes')

        if verbose:
            print(f'✅ Preprocessing completed, final size: {HORUS.shape[0]} earthquakes')

        return HORUS, T1, T2

    @staticmethod
    def create_catalogs(HORUS, params, learn_start_year, learn_end_year, catalog_start_year):
        """
        Create sub-catalogs from preprocessed earthquake catalog (without spatial filtering).

        This function creates three sub-catalogs for EEPAS learning. When no RegionManager
        is provided, all events are treated as being within both the Neighborhood Region
        and Testing Region (no spatial filtering applied).

        Naming conventions (from main_gji.tex paper):
            - Index i: Historical source events (CatI), from Neighborhood Region N
            - Index j: Target events (CatJ), from Testing Region R
            - NLL = -Σ_j log λ(t_j, m_j, x_j, y_j | CatI) + ∫∫∫∫_R λ(...) dt dm dx dy

        Args:
            HORUS: Preprocessed earthquake catalog (numpy array, N×11)
            params: Model parameters dictionary, must contain 'mT' (target magnitude threshold)
            learn_start_year: Learning start year
            learn_end_year: Learning end year
            catalog_start_year: Catalog start year (for time conversion)

        Returns:
            tuple: (CatE, CatI, CatJ)

                - CatE: EEPAS precursor catalog (M≥m₀, all time)
                - CatI: Historical source events (M≥mT, all time, Neighborhood Region) - paper's index i
                - CatJ: Target events (M≥mT, learning period, Testing Region) - paper's index j

        Note:
            Return order is (CatE, CatI, CatJ), corresponding to (precursor, i, j) in paper.
            This differs from versions before v1.1.0 (old order was CatE, CatJ, CatI).
        """
        print('Creating sub-catalogs for different purposes...')

        # 1. EEPAS catalog - contains all preprocessed earthquakes
        CatE = HORUS.copy()

        # 2. Historical source catalog (paper's i) - events with magnitude >= mT in neighborhood region
        CatI = HORUS.copy()
        target_mag_filter = CatI[:, 9] >= params['mT']  # Column 10 is magnitude (index 9)
        CatI = CatI[target_mag_filter, :]

        # 3. Target catalog (paper's j) - earthquakes during learning period with magnitude >= mT in testing region
        CatJ = HORUS.copy()

        # Filter events before learning start time
        learning_start_filter = CatJ[:, 0] >= learn_start_year  # Column 1 is year (index 0)
        CatJ = CatJ[learning_start_filter, :]

        # Filter events below target magnitude
        target_mag_filter_J = CatJ[:, 9] >= params['mT']
        CatJ = CatJ[target_mag_filter_J, :]

        # Output statistics
        print('Catalog creation completed:')
        print(f'  EEPAS catalog (CatE): {CatE.shape[0]} events')
        print(f'  Historical source catalog (CatI): {CatI.shape[0]} events (magnitude >= {params["mT"]}) - paper\'s i')
        print(f'  Target catalog (CatJ): {CatJ.shape[0]} events (learning period, magnitude >= {params["mT"]}) - paper\'s j')

        return CatE, CatI, CatJ

    @staticmethod
    def filter_by_region(catalog, region_manager, region_type='testing', x_col=7, y_col=6):
        """
        Filter earthquake catalog by spatial region.

        Purpose:

            - Integrates with RegionManager for spatial filtering
            - Automatically handles both grid and polygon region formats

        Args:
            catalog: numpy array (N×M) earthquake catalog
                     HORUS format: [..., y(col6), x(col7), depth(col8), mag(col9), ...]
            region_manager: RegionManager instance
            region_type: 'testing' or 'neighborhood'

                - 'testing': filter events within testing region (for target events)
                - 'neighborhood': filter events within neighborhood region (for source events)

            x_col: X coordinate column (default 7)
            y_col: Y coordinate column (default 6)

        Returns:
            numpy.ndarray: Filtered earthquake catalog
        """
        if region_type == 'testing':
            return region_manager.filter_events_for_targets(catalog, x_col, y_col)
        elif region_type == 'neighborhood':
            return region_manager.filter_events_for_learning(catalog, x_col, y_col)
        else:
            raise ValueError(
                f"Unsupported region_type: {region_type}. "
                f"Must be 'testing' or 'neighborhood'"
            )

    @staticmethod
    def create_catalogs_with_regions(HORUS, params, learn_start_year, learn_end_year,
                                     catalog_start_year, region_manager=None):
        """
        Create sub-catalogs from preprocessed earthquake catalog (with optional spatial filtering).

        This function supports both spatial filtering modes depending on the region_manager parameter.
        When region_manager is None, all events are used without spatial filtering.
        When region_manager is provided, events are filtered by Neighborhood and Testing Regions.

        Naming conventions (from main_gji.tex paper):

            - Index i: Historical source events (CatI), from Neighborhood Region N
            - Index j: Target events (CatJ), from Testing Region R
            - NLL = -Σ_j log λ(t_j, m_j, x_j, y_j | CatI) + ∫∫∫∫_R λ(...) dt dm dx dy

        Difference from create_catalogs():

            - Supports RegionManager spatial filtering
            - Without region_manager (None): Behaves identically to create_catalogs()
            - With region_manager provided:

                * CatE: All events within Neighborhood Region N (for edge compensation)
                * CatI: M≥mT events within Neighborhood Region N (historical sources, paper's index i)
                * CatJ: M≥mT events within Testing Region R during learning period (targets, paper's index j)

        Args:
            HORUS: Preprocessed earthquake catalog (numpy array, N×11)
            params: Model parameters dictionary, must contain 'mT' (target magnitude threshold)
            learn_start_year: Learning start year
            learn_end_year: Learning end year
            catalog_start_year: Catalog start year (for time conversion)
            region_manager: RegionManager instance (optional)

                - None: No spatial filtering applied
                - RegionManager: Apply spatial filtering using Neighborhood and Testing Regions

        Returns:
            tuple: (CatE, CatI, CatJ) containing:

                - CatE: EEPAS precursor catalog (M≥m₀)
                - CatI: Historical source events (M≥mT, Neighborhood Region) - paper's index i
                - CatJ: Target events (M≥mT, learning period, Testing Region) - paper's index j

        Note:
            Return order is (CatE, CatI, CatJ), corresponding to (precursor, i, j) in paper.
            This differs from versions before v1.1.0 (old order was CatE, CatJ, CatI).
        """
        print('Creating sub-catalogs for different purposes...')

        if region_manager is None:
            # No spatial filtering: backward compatible, use original logic
            return CatalogProcessor.create_catalogs(
                HORUS, params, learn_start_year, learn_end_year, catalog_start_year
            )

        # With spatial filtering: use RegionManager to filter events by spatial regions
        print('  Using spatial region filtering')

        # 1. EEPAS catalog - all events within neighborhood region (for edge compensation)
        CatE = CatalogProcessor.filter_by_region(
            HORUS, region_manager, region_type='neighborhood'
        )

        # 2. Historical source catalog (paper's i) - events with magnitude >= mT within neighborhood region
        CatI = CatE.copy()
        target_mag_filter = CatI[:, 9] >= params['mT']
        CatI = CatI[target_mag_filter, :]

        # 3. Target catalog (paper's j) - events with magnitude >= mT during learning period within testing region
        # First filter by time range
        CatJ_time_filtered = HORUS.copy()
        learning_start_filter = CatJ_time_filtered[:, 0] >= learn_start_year
        CatJ_time_filtered = CatJ_time_filtered[learning_start_filter, :]

        # Then filter by magnitude
        target_mag_filter_J = CatJ_time_filtered[:, 9] >= params['mT']
        CatJ_time_filtered = CatJ_time_filtered[target_mag_filter_J, :]

        # Finally filter by spatial region (testing region)
        CatJ = CatalogProcessor.filter_by_region(
            CatJ_time_filtered, region_manager, region_type='testing'
        )

        # Output statistics
        print('Catalog creation completed:')
        print(f'  EEPAS catalog (CatE): {CatE.shape[0]} events '
              f'(neighborhood region, all magnitudes)')
        print(f'  Historical source catalog (CatI): {CatI.shape[0]} events '
              f'(neighborhood region, magnitude >= {params["mT"]}) - paper\'s i')
        print(f'  Target catalog (CatJ): {CatJ.shape[0]} events '
              f'(testing region, learning period, magnitude >= {params["mT"]}) - paper\'s j')

        return CatE, CatI, CatJ

    @staticmethod
    def filter_by_magnitude(catalog, min_magnitude, mag_col=9):
        """
        Filter earthquake catalog by magnitude.

        Args:
            catalog: numpy array earthquake catalog
            min_magnitude: Minimum magnitude threshold
            mag_col: Magnitude column (default 9)

        Returns:
            numpy array: Filtered catalog
        """
        mag_filter = catalog[:, mag_col] >= min_magnitude
        return catalog[mag_filter]

    @staticmethod
    def filter_by_time_range(catalog, start_year, end_year, year_col=0):
        """
        Filter earthquake catalog by time range.

        Args:
            catalog: numpy array earthquake catalog
            start_year: Start year
            end_year: End year
            year_col: Year column (default 0)

        Returns:
            numpy array: Filtered catalog
        """
        time_filter = (catalog[:, year_col] >= start_year) & (catalog[:, year_col] < end_year)
        return catalog[time_filter]

    # ========================================================================
    # Format Conversion Methods (delegated to catalog_processor_extensions)
    # ========================================================================

    @staticmethod
    def from_zmap(file_path, delimiter=None, skiprows=0):
        """Read ZMAP format and convert to HORUS format. See catalog_processor_extensions.from_zmap()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_zmap(file_path, delimiter, skiprows)

    @staticmethod
    def from_csep(file_path):
        """Read CSEP ASCII format and convert to HORUS format. See catalog_processor_extensions.from_csep()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_csep(file_path)

    @staticmethod
    def from_quakeml(file_path):
        """Read QuakeML format and convert to HORUS format. See catalog_processor_extensions.from_quakeml()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_quakeml(file_path)

    @staticmethod
    def from_dataframe(df, column_mapping=None):
        """Convert Pandas DataFrame to HORUS format. See catalog_processor_extensions.from_dataframe()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_dataframe(df, column_mapping)

    @staticmethod
    def from_horus_text(file_path, delimiter=None, skiprows=0):
        """Read HORUS text format. See catalog_processor_extensions.from_horus_text()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_horus_text(file_path, delimiter, skiprows)

    @staticmethod
    def from_ingv_horus(file_path, delimiter='\t', skiprows=1, filter_events=True):
        """Read INGV HORUS catalog format. See catalog_processor_extensions.from_ingv_horus()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_ingv_horus(file_path, delimiter, skiprows, filter_events)

    @staticmethod
    def from_seismostats(catalog):
        """Convert SeismoStats Catalog object to HORUS format. See catalog_processor_extensions.from_seismostats()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_seismostats(catalog)

    @staticmethod
    def from_pycsep(catalog):
        """Convert pyCSEP CSEPCatalog object to HORUS format. See catalog_processor_extensions.from_pycsep()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_pycsep(catalog)

    @staticmethod
    def from_mat(file_path, variable_name='HORUS'):
        """Read HORUS catalog from MATLAB .mat file. See catalog_processor_extensions.from_mat()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.from_mat(file_path, variable_name)

    @staticmethod
    def to_seismostats(horus_catalog, mc=None, delta_m=0.1, b_value=None, a_value=None):
        """Convert HORUS format to SeismoStats Catalog object. See catalog_processor_extensions.to_seismostats()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.to_seismostats(horus_catalog, mc, delta_m, b_value, a_value)

    @staticmethod
    def to_pycsep(horus_catalog, name='EEPAS_catalog', region=None):
        """Convert HORUS format to pyCSEP CSEPCatalog object. See catalog_processor_extensions.to_pycsep()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.to_pycsep(horus_catalog, name, region)

    @staticmethod
    def to_mat(horus_catalog, output_file, variable_name='HORUS', matlab_compatible=True):
        """Write HORUS format catalog to MATLAB .mat file. See catalog_processor_extensions.to_mat()"""
        if not _EXTENSIONS_AVAILABLE:
            raise ImportError("catalog_processor_extensions module not available")
        return ext.to_mat(horus_catalog, output_file, variable_name, matlab_compatible)

    @staticmethod
    def detect_format(file_path):
        """
        Auto-detect earthquake catalog file format based on extension and content.

        Args:
            file_path: Path to catalog file

        Returns:
            str: Detected format ('zmap', 'csep', 'quakeml', 'horus', 'mat', 'unknown')
        """
        import os

        # Check file extension
        ext_lower = os.path.splitext(file_path)[1].lower()

        if ext_lower in ['.mat']:
            return 'mat'
        elif ext_lower in ['.xml', '.quakeml']:
            return 'quakeml'
        elif ext_lower in ['.zmap']:
            return 'zmap'
        elif ext_lower in ['.csep']:
            return 'csep'
        elif ext_lower in ['.txt', '.dat', '.catalog']:
            # Try to detect from content
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline().strip()
                    # Check if contains ISO timestamp (CSEP format indicator)
                    if 'T' in first_line and ('Z' in first_line or '-' in first_line[:10]):
                        return 'csep'
                    # Otherwise assume HORUS text format
                    return 'horus'
            except:
                return 'unknown'
        else:
            return 'unknown'
