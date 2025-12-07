"""
Catalog Format Converters - Extended format support for CatalogProcessor

This module contains format conversion functions for various earthquake catalog formats.
All converters output standard HORUS format for compatibility with existing pipeline.
"""

import numpy as np
from datetime import datetime, timedelta


def from_zmap(file_path, delimiter=None, skiprows=0):
    """
    Read ZMAP format and convert to HORUS format.

    ZMAP format (10 columns):
        lon, lat, year, month, day, mag, depth, hour, minute, second

    HORUS format (10 columns):
        year, month, day, hour, minute, second, lat, lon, depth, mag

    Args:
        file_path: Path to ZMAP file
        delimiter: Column delimiter (None=auto-detect, '\t', ' ', ',')
        skiprows: Number of header rows to skip (default 0)

    Returns:
        np.ndarray: HORUS format catalog

    Examples:
        >>> cat = from_zmap('catalog.zmap')
        >>> print(cat.shape)  # (N, 10)

    References:
        ObsPy ZMAP documentation: https://docs.obspy.org/packages/obspy.io.zmap.html
    """
    # Auto-detect delimiter from first line
    if delimiter is None:
        with open(file_path, 'r') as f:
            # Skip header lines
            for _ in range(skiprows):
                f.readline()
            first_line = f.readline().strip()

        if '\t' in first_line:
            delimiter = '\t'
        elif ',' in first_line:
            delimiter = ','
        else:
            delimiter = None  # numpy handles whitespace

    # Read data
    try:
        data = np.loadtxt(file_path, delimiter=delimiter, skiprows=skiprows)

        if data.ndim == 1:
            data = data.reshape(1, -1)

        # Check column count
        if data.shape[1] < 10:
            raise ValueError(
                f"ZMAP file must have at least 10 columns, got {data.shape[1]}"
            )

        # Take only first 10 columns
        data = data[:, :10]

        # ZMAP columns: lon, lat, year, month, day, mag, depth, hour, minute, second
        lon = data[:, 0]
        lat = data[:, 1]
        year = data[:, 2]
        month = data[:, 3]
        day = data[:, 4]
        mag = data[:, 5]
        depth = data[:, 6]
        hour = data[:, 7]
        minute = data[:, 8]
        second = data[:, 9]

        # Convert decimal year to integer year
        # ZMAP year column can be decimal year or integer year
        # If all values > 3000, treat as decimal year (e.g., 2025.9023)
        if np.mean(year) > 3000:
            # Decimal year format
            year_int = year.astype(int)
        else:
            year_int = year

        # Rearrange to HORUS format
        horus = np.column_stack([
            year_int, month, day, hour, minute, second,  # Time (cols 0-5)
            lat, lon, depth, mag  # Space & magnitude (cols 6-9)
        ])

        print(f"✅ Loaded ZMAP catalog: {horus.shape[0]} events from {file_path}")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read ZMAP file {file_path}: {e}")


def from_csep(file_path):
    """
    Read CSEP ASCII format and convert to HORUS format.

    Supports two CSEP format variants:
        1. Space-separated: lon lat mag origin_time depth
        2. CSV format: lon,lat,mag,time_string,depth,catalog_id,event_id

    origin_time: ISO format (YYYY-MM-DDTHH:MM:SS.fff or YYYY-MM-DDTHH:MM:SS.fffZ)

    Args:
        file_path: Path to CSEP file

    Returns:
        np.ndarray: HORUS format catalog

    Examples:
        >>> cat = from_csep('catalog.csep')
        >>> print(cat.shape)  # (N, 10)

    References:
        PyCSEP documentation: https://docs.cseptesting.org/concepts/catalogs.html
    """
    events = []
    line_num = 0

    with open(file_path, 'r') as f:
        for line in f:
            line_num += 1
            line = line.strip()
            # Skip comments, headers, and empty lines
            if not line or line.startswith('#') or 'lon' in line.lower() and 'lat' in line.lower():
                continue

            # Try to detect delimiter (comma or space)
            if ',' in line:
                # CSV format
                parts = [p.strip().strip('"') for p in line.split(',')]
            else:
                # Space-separated format
                parts = line.split()

            if len(parts) < 4:
                continue

            try:
                lon = float(parts[0])
                lat = float(parts[1])
                mag = float(parts[2])
                time_str = parts[3]
                depth = float(parts[4]) if len(parts) > 4 else 10.0

                # Parse ISO time format
                # Format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.fff
                # May have 'Z' suffix for UTC
                time_str = time_str.replace('Z', '')

                # Handle different precision
                if '.' in time_str:
                    # Has fractional seconds
                    dt = datetime.fromisoformat(time_str)
                else:
                    # Integer seconds only
                    dt = datetime.fromisoformat(time_str)

                # Convert to HORUS format
                events.append([
                    dt.year, dt.month, dt.day,
                    dt.hour, dt.minute, dt.second + dt.microsecond / 1e6,
                    lat, lon, depth, mag
                ])

            except Exception as e:
                if line_num <= 10:  # Only show warnings for first 10 lines
                    print(f"Warning: Failed to parse line {line_num}: {line[:50]}... ({e})")
                continue

    if not events:
        raise ValueError(f"No valid events found in CSEP file: {file_path}")

    horus = np.array(events)
    print(f"✅ Loaded CSEP catalog: {horus.shape[0]} events from {file_path}")
    return horus


def from_dataframe(df, column_mapping=None):
    """
    Convert Pandas DataFrame to HORUS format.

    Args:
        df: Pandas DataFrame
        column_mapping: dict, optional column name mapping
            Example: {'lon': 'longitude', 'lat': 'latitude', 'mag': 'magnitude'}

    Required columns (after mapping):
        - longitude (or lon)
        - latitude (or lat)
        - magnitude (or mag)
        - time: datetime object, decimal year, or separate (year, month, day...)
        - depth (optional, default 10 km)

    Returns:
        np.ndarray: HORUS format catalog

    Examples:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'longitude': [121.5, 122.0],
        ...     'latitude': [24.0, 24.5],
        ...     'magnitude': [5.0, 5.5],
        ...     'time': pd.to_datetime(['2020-01-01', '2020-01-02'])
        ... })
        >>> cat = from_dataframe(df)
        >>> print(cat.shape)  # (2, 10)
    """
    import pandas as pd

    df = df.copy()

    # Apply column mapping
    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Standardize column names
    if 'lon' in df.columns and 'longitude' not in df.columns:
        df['longitude'] = df['lon']
    if 'lat' in df.columns and 'latitude' not in df.columns:
        df['latitude'] = df['lat']
    if 'mag' in df.columns and 'magnitude' not in df.columns:
        df['magnitude'] = df['mag']

    # Check required columns
    required = ['longitude', 'latitude', 'magnitude']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Handle time column
    if 'time' in df.columns:
        # If datetime object
        if pd.api.types.is_datetime64_any_dtype(df['time']):
            dt = pd.to_datetime(df['time'])
            year = dt.dt.year.values
            month = dt.dt.month.values
            day = dt.dt.day.values
            hour = dt.dt.hour.values
            minute = dt.dt.minute.values
            second = dt.dt.second.values + dt.dt.microsecond.values / 1e6

        # If decimal year
        elif pd.api.types.is_numeric_dtype(df['time']):
            year, month, day, hour, minute, second = \
                _decimal_year_to_calendar(df['time'].values)
        else:
            raise ValueError("Unsupported time format in DataFrame")

    # Or separate year/month/day columns
    elif all(col in df.columns for col in ['year', 'month', 'day']):
        year = df['year'].values
        month = df['month'].values
        day = df['day'].values
        hour = df['hour'].values if 'hour' in df.columns else np.zeros(len(df))
        minute = df['minute'].values if 'minute' in df.columns else np.zeros(len(df))
        second = df['second'].values if 'second' in df.columns else np.zeros(len(df))
    else:
        raise ValueError(
            "DataFrame must have 'time' column or (year, month, day) columns"
        )

    # Handle depth
    depth = df['depth'].values if 'depth' in df.columns else np.full(len(df), 10.0)

    # Assemble HORUS format
    horus = np.column_stack([
        year, month, day, hour, minute, second,
        df['latitude'].values, df['longitude'].values, depth, df['magnitude'].values
    ])

    print(f"✅ Converted DataFrame to HORUS: {horus.shape[0]} events")
    return horus


def from_horus_text(file_path, delimiter=None, skiprows=0):
    """
    Read HORUS text format.

    HORUS format (10 columns):
        year, month, day, hour, minute, second, lat, lon, depth, mag

    Args:
        file_path: Path to HORUS text file
        delimiter: Column delimiter (None=whitespace)
        skiprows: Number of header rows to skip

    Returns:
        np.ndarray: HORUS format catalog
    """
    try:
        data = np.loadtxt(file_path, delimiter=delimiter, skiprows=skiprows)

        if data.ndim == 1:
            data = data.reshape(1, -1)

        if data.shape[1] < 10:
            raise ValueError(
                f"HORUS file must have at least 10 columns, got {data.shape[1]}"
            )

        # Take first 10 columns
        horus = data[:, :10]

        print(f"✅ Loaded HORUS text catalog: {horus.shape[0]} events from {file_path}")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read HORUS text file {file_path}: {e}")


def _decimal_year_to_calendar(decimal_years):
    """
    Convert decimal year to calendar date.

    Args:
        decimal_years: np.array of decimal years

    Returns:
        tuple: (year, month, day, hour, minute, second) as numpy arrays
    """
    n = len(decimal_years)
    year = np.zeros(n, dtype=int)
    month = np.zeros(n, dtype=int)
    day = np.zeros(n, dtype=int)
    hour = np.zeros(n, dtype=int)
    minute = np.zeros(n, dtype=int)
    second = np.zeros(n, dtype=float)

    for i, dy in enumerate(decimal_years):
        y = int(dy)
        fraction = dy - y

        start_of_year = datetime(y, 1, 1)
        # Check if leap year
        is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
        days_in_year = 366 if is_leap else 365

        day_of_year = fraction * days_in_year
        dt = start_of_year + timedelta(days=day_of_year)

        year[i] = dt.year
        month[i] = dt.month
        day[i] = dt.day
        hour[i] = dt.hour
        minute[i] = dt.minute
        second[i] = dt.second + dt.microsecond / 1e6

    return year, month, day, hour, minute, second


def from_quakeml(file_path):
    """
    Read QuakeML format and convert to HORUS format.

    QuakeML is an XML-based standard format for seismological data.
    This function uses ObsPy to parse QuakeML files.

    Args:
        file_path: Path to QuakeML file (.xml)

    Returns:
        np.ndarray: HORUS format catalog

    Examples:
        >>> cat = from_quakeml('earthquakes.xml')
        >>> print(cat.shape)  # (N, 10)

    Raises:
        ImportError: If obspy is not installed
        ValueError: If no valid events found

    References:
        ObsPy QuakeML documentation: https://docs.obspy.org/packages/obspy.io.quakeml.html

    .. note::
       Requires obspy package: `pip install obspy`
    """
    try:
        from obspy import read_events
    except ImportError:
        raise ImportError(
            "QuakeML format requires 'obspy' package. "
            "Install with: pip install obspy"
        )

    try:
        # Read QuakeML file using ObsPy
        catalog = read_events(file_path, format='QUAKEML')

        if len(catalog) == 0:
            raise ValueError(f"No events found in QuakeML file: {file_path}")

        events = []

        for event in catalog:
            # Get preferred origin (or first origin)
            origin = event.preferred_origin() or event.origins[0] if event.origins else None
            if origin is None:
                continue

            # Get preferred magnitude (or first magnitude)
            magnitude = event.preferred_magnitude() or event.magnitudes[0] if event.magnitudes else None
            if magnitude is None:
                continue

            # Extract time
            origin_time = origin.time
            dt = origin_time.datetime

            # Extract location
            lat = origin.latitude
            lon = origin.longitude
            depth = origin.depth / 1000.0 if origin.depth is not None else 10.0  # Convert m to km

            # Extract magnitude
            mag = magnitude.mag

            # Convert to HORUS format
            events.append([
                dt.year, dt.month, dt.day,
                dt.hour, dt.minute, dt.second + dt.microsecond / 1e6,
                lat, lon, depth, mag
            ])

        if not events:
            raise ValueError(f"No valid events with origin and magnitude found in: {file_path}")

        horus = np.array(events)
        print(f"✅ Loaded QuakeML catalog: {horus.shape[0]} events from {file_path}")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read QuakeML file {file_path}: {e}")


def to_seismostats(horus_catalog, mc=None, delta_m=0.1, b_value=None, a_value=None):
    """
    Convert HORUS format catalog to SeismoStats Catalog object.

    Args:
        horus_catalog: HORUS format catalog (N x 10 numpy array)
                      [year, month, day, hour, minute, second, lat, lon, depth, mag]
        mc: Completeness magnitude (optional)
        delta_m: Magnitude precision (default 0.1)
        b_value: Gutenberg-Richter b-value (optional)
        a_value: Gutenberg-Richter a-value (optional)

    Returns:
        SeismoStats.Catalog: Catalog object (inherits from pandas.DataFrame)

    Examples:
        >>> horus = CatalogProcessor.load_catalog('earthquakes.zmap')
        >>> catalog = to_seismostats(horus, mc=2.5, delta_m=0.1)
        >>> print(catalog.head())  # Catalog itself is a DataFrame

    Raises:
        ImportError: If SeismoStats is not installed

    References:
        SeismoStats documentation: https://seismostats.readthedocs.io/

    .. note::
       Requires SeismoStats package: `pip install seismostats`
       Catalog class inherits from pandas.DataFrame, no .df attribute needed
    """
    try:
        from seismostats import Catalog
    except ImportError:
        raise ImportError(
            "seismostats package is required. "
            "Install with: pip install seismostats"
        )

    import pandas as pd

    # Extract columns from HORUS format
    year = horus_catalog[:, 0].astype(int)
    month = horus_catalog[:, 1].astype(int)
    day = horus_catalog[:, 2].astype(int)
    hour = horus_catalog[:, 3].astype(int)
    minute = horus_catalog[:, 4].astype(int)
    second = horus_catalog[:, 5]
    latitude = horus_catalog[:, 6]
    longitude = horus_catalog[:, 7]
    depth = horus_catalog[:, 8]
    magnitude = horus_catalog[:, 9]

    # Create datetime objects
    times = []
    for i in range(len(horus_catalog)):
        microsecond = int((second[i] % 1) * 1e6)
        dt = datetime(year[i], month[i], day[i],
                     hour[i], minute[i], int(second[i]), microsecond)
        times.append(dt)

    # Create DataFrame with SeismoStats standard columns
    df = pd.DataFrame({
        'time': pd.to_datetime(times),
        'latitude': latitude,
        'longitude': longitude,
        'depth': depth,
        'magnitude': magnitude
    })

    # Create Catalog object with optional parameters
    catalog = Catalog(
        data=df,
        mc=mc,
        delta_m=delta_m,
        b_value=b_value,
        a_value=a_value
    )

    print(f"✅ Converted to SeismoStats Catalog: {len(catalog)} events")
    return catalog


def to_pycsep(horus_catalog, name='EEPAS_catalog', region=None):
    """
    Convert HORUS format catalog to pyCSEP CSEPCatalog object.

    Args:
        horus_catalog: HORUS format catalog (N x 10 numpy array)
                      [year, month, day, hour, minute, second, lat, lon, depth, mag]
        name: Catalog name (default 'EEPAS_catalog')
        region: Optional spatial region (csep.core.regions.CartesianGrid2D)

    Returns:
        csep.core.catalogs.CSEPCatalog: CSEPCatalog object

    Examples:
        >>> horus = CatalogProcessor.load_catalog('earthquakes.zmap')
        >>> catalog = to_pycsep(horus, name='Italy_2020')
        >>> print(catalog.get_number_of_events())

    Raises:
        ImportError: If pycsep is not installed

    References:
        PyCSEP documentation: https://docs.cseptesting.org/

    .. note::
       Requires pycsep package: `pip install pycsep`
    """
    try:
        import csep
        from csep.core.catalogs import CSEPCatalog
    except ImportError:
        raise ImportError(
            "pycsep package is required. "
            "Install with: pip install pycsep"
        )

    # Extract columns from HORUS format
    year = horus_catalog[:, 0].astype(int)
    month = horus_catalog[:, 1].astype(int)
    day = horus_catalog[:, 2].astype(int)
    hour = horus_catalog[:, 3].astype(int)
    minute = horus_catalog[:, 4].astype(int)
    second = horus_catalog[:, 5]
    latitude = horus_catalog[:, 6]
    longitude = horus_catalog[:, 7]
    depth = horus_catalog[:, 8]
    magnitude = horus_catalog[:, 9]

    # Create event list in pyCSEP format
    # CSEPCatalog uses structured numpy array with dtype:
    # [('id', 'S256'), ('origin_time', '<i8'), ('latitude', '<f4'),
    #  ('longitude', '<f4'), ('depth', '<f4'), ('magnitude', '<f4')]

    n_events = len(horus_catalog)
    eventlist = np.zeros(n_events, dtype=[
        ('id', 'S256'),
        ('origin_time', '<i8'),
        ('latitude', '<f4'),
        ('longitude', '<f4'),
        ('depth', '<f4'),
        ('magnitude', '<f4')
    ])

    for i in range(n_events):
        # Generate event ID
        event_id = f"event_{i:06d}".encode('utf-8')

        # Convert time to Unix timestamp (milliseconds since epoch)
        microsecond = int((second[i] % 1) * 1e6)
        dt = datetime(year[i], month[i], day[i],
                     hour[i], minute[i], int(second[i]), microsecond)
        # pyCSEP uses milliseconds since epoch
        origin_time = int(dt.timestamp() * 1000)

        eventlist[i] = (
            event_id,
            origin_time,
            latitude[i],
            longitude[i],
            depth[i],
            magnitude[i]
        )

    # Create CSEPCatalog object
    catalog = CSEPCatalog(data=eventlist, name=name, region=region)

    print(f"✅ Converted to pyCSEP CSEPCatalog: {catalog.get_number_of_events()} events")
    return catalog


def from_seismostats(catalog):
    """
    Convert SeismoStats Catalog object to HORUS format.

    Args:
        catalog: SeismoStats.Catalog object (inherits from pandas.DataFrame)

    Returns:
        np.ndarray: HORUS format catalog (N x 10 array)
                   [year, month, day, hour, minute, second, lat, lon, depth, mag]

    Examples:
        >>> from seismostats import Catalog
        >>> catalog = Catalog.from_quakeml('earthquakes.xml')
        >>> horus = from_seismostats(catalog)
        >>> print(horus.shape)  # (N, 10)

    Raises:
        ImportError: If SeismoStats is not installed
        ValueError: If required columns are missing

    References:
        SeismoStats documentation: https://seismostats.readthedocs.io/

    .. note::
       Requires SeismoStats package: `pip install seismostats`
       Catalog class inherits from pandas.DataFrame, access columns directly
    """
    try:
        from seismostats import Catalog
    except ImportError:
        raise ImportError(
            "seismostats package is required. "
            "Install with: pip install seismostats"
        )

    import pandas as pd

    # Catalog itself is a DataFrame (inherits from pandas.DataFrame)
    # Check required columns
    required = ['time', 'latitude', 'longitude', 'magnitude']
    missing = [col for col in required if col not in catalog.columns]
    if missing:
        raise ValueError(f"Missing required columns in SeismoStats Catalog: {missing}")

    # Convert time to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(catalog['time']):
        time_col = pd.to_datetime(catalog['time'])
    else:
        time_col = catalog['time']

    dt = pd.to_datetime(time_col)

    # Extract time components
    year = dt.dt.year.values
    month = dt.dt.month.values
    day = dt.dt.day.values
    hour = dt.dt.hour.values
    minute = dt.dt.minute.values
    second = dt.dt.second.values + dt.dt.microsecond.values / 1e6

    # Extract spatial components
    latitude = catalog['latitude'].values
    longitude = catalog['longitude'].values
    depth = catalog['depth'].values if 'depth' in catalog.columns else np.full(len(catalog), 10.0)
    magnitude = catalog['magnitude'].values

    # Assemble HORUS format
    horus = np.column_stack([
        year, month, day, hour, minute, second,
        latitude, longitude, depth, magnitude
    ])

    print(f"✅ Converted from SeismoStats Catalog: {horus.shape[0]} events")
    return horus


def from_pycsep(catalog):
    """
    Convert pyCSEP CSEPCatalog object to HORUS format.

    Args:
        catalog: csep.core.catalogs.CSEPCatalog object

    Returns:
        np.ndarray: HORUS format catalog (N x 10 array)
                   [year, month, day, hour, minute, second, lat, lon, depth, mag]

    Examples:
        >>> from csep.core.catalogs import CSEPCatalog
        >>> catalog = CSEPCatalog.load_ascii('earthquakes.csep')
        >>> horus = from_pycsep(catalog)
        >>> print(horus.shape)  # (N, 10)

    Raises:
        ImportError: If pycsep is not installed

    References:
        PyCSEP documentation: https://docs.cseptesting.org/

    .. note::
       Requires pycsep package: `pip install pycsep`
    """
    try:
        from csep.core.catalogs import CSEPCatalog
    except ImportError:
        raise ImportError(
            "pycsep package is required. "
            "Install with: pip install pycsep"
        )

    # Get event data from CSEPCatalog
    # CSEPCatalog stores data in structured numpy array with fields:
    # id, origin_time, latitude, longitude, depth, magnitude
    events = catalog.catalog

    n_events = len(events)
    horus = np.zeros((n_events, 10))

    for i, event in enumerate(events):
        # Convert Unix timestamp (milliseconds) to datetime
        timestamp_ms = event['origin_time']
        dt = datetime.fromtimestamp(timestamp_ms / 1000.0)

        # Extract components
        horus[i, 0] = dt.year
        horus[i, 1] = dt.month
        horus[i, 2] = dt.day
        horus[i, 3] = dt.hour
        horus[i, 4] = dt.minute
        horus[i, 5] = dt.second + dt.microsecond / 1e6

        # Spatial components
        horus[i, 6] = event['latitude']
        horus[i, 7] = event['longitude']
        horus[i, 8] = event['depth']
        horus[i, 9] = event['magnitude']

    print(f"✅ Converted from pyCSEP CSEPCatalog: {horus.shape[0]} events")
    return horus


def from_ingv_horus(file_path, delimiter='\t', skiprows=1, filter_events=True):
    """
    Read INGV HORUS catalog format and convert to internal HORUS format.

    INGV HORUS format (15 columns, tab-separated):
        Year, Mo, Da, Ho, Mi, Se, Lat, Lon, Depth, Mw, sigMw, Geo-Ita, Geo-CPTI15, Ev. type, Iside n.

    Internal HORUS format (10 columns):
        year, month, day, hour, minute, second, lat, lon, depth, mag

    Args:
        file_path: Path to INGV HORUS catalog file
        delimiter: Column delimiter (default '\t' for tab-separated)
        skiprows: Number of header rows to skip (default 1)
        filter_events: Remove non-earthquake events (marked with 'x' in column 14) (default True)

    Returns:
        np.ndarray: Internal HORUS format catalog (N x 10)

    Examples:
        >>> cat = from_ingv_horus('HORUS_Ita_Catalog.txt')
        >>> print(cat.shape)  # (N, 10)

    References:
        INGV HORUS catalog: https://doi.org/10.13127/horus
        Lolli et al. (2020), SRL, 91, 3208-3222, doi: 10.1785/0220200148

    .. note::
       The INGV HORUS catalog includes homogenized moment magnitudes (Mw) computed
       from various magnitude types in the INGV bulletin (ISIDe).
    """
    import pandas as pd

    try:
        # Read with pandas to handle mixed types (numbers and symbols)
        df = pd.read_csv(file_path, delimiter=delimiter, skiprows=skiprows, header=None)

        # Expected 15 columns (some files might have 13-15 depending on version)
        n_cols = df.shape[1]
        if n_cols < 10:
            raise ValueError(
                f"INGV HORUS file must have at least 10 columns, got {n_cols}"
            )

        # Extract first 10 columns (time + location + magnitude)
        year = df.iloc[:, 0].values
        month = df.iloc[:, 1].values
        day = df.iloc[:, 2].values
        hour = df.iloc[:, 3].values
        minute = df.iloc[:, 4].values
        second = df.iloc[:, 5].values
        lat = df.iloc[:, 6].values
        lon = df.iloc[:, 7].values
        depth = df.iloc[:, 8].values
        mag = df.iloc[:, 9].values

        # Filter non-earthquake events if requested (column 13, 0-indexed column 13)
        if filter_events and n_cols >= 14:
            # Column 14 (index 13): 'x' indicates non-earthquake event
            event_type = df.iloc[:, 13].fillna('').astype(str).str.strip()
            is_earthquake = event_type != 'x'

            year = year[is_earthquake]
            month = month[is_earthquake]
            day = day[is_earthquake]
            hour = hour[is_earthquake]
            minute = minute[is_earthquake]
            second = second[is_earthquake]
            lat = lat[is_earthquake]
            lon = lon[is_earthquake]
            depth = depth[is_earthquake]
            mag = mag[is_earthquake]

            n_filtered = (~is_earthquake).sum()
            if n_filtered > 0:
                print(f"  Filtered {n_filtered} non-earthquake events")

        # Assemble internal HORUS format
        horus = np.column_stack([
            year, month, day, hour, minute, second,
            lat, lon, depth, mag
        ])

        print(f"✅ Loaded INGV HORUS catalog: {horus.shape[0]} events from {file_path}")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read INGV HORUS file {file_path}: {e}")


def to_mat(horus_catalog, output_file, variable_name='HORUS', matlab_compatible=True):
    """
    Write HORUS format catalog to MATLAB .mat file.

    The output format is identical to existing EEPAS data files:
        - MATLAB v7.3 format (HDF5-based) if matlab_compatible=True
        - Contains single variable with specified name
        - Array shape: (N, 10) where N is number of events

    Args:
        horus_catalog: HORUS format catalog (N x 10 numpy array)
                      [year, month, day, hour, minute, second, lat, lon, depth, mag]
        output_file: Output .mat file path
        variable_name: Variable name in MAT file (default 'HORUS')
        matlab_compatible: Use MATLAB v7.3 format for compatibility (default True)

    Examples:
        >>> cat = CatalogProcessor.load_catalog('earthquakes.zmap')
        >>> to_mat(cat, 'output.mat', variable_name='HORUS')
        >>> # Result can be loaded in MATLAB: load('output.mat')

    References:
        scipy.io.savemat documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.savemat.html

    .. note::
       The output format matches existing EEPAS .mat files in the data/ directory.
       Compatible with both Python (scipy.io.loadmat) and MATLAB.
    """
    import scipy.io as sio

    # Validate input
    if horus_catalog.shape[1] not in [10, 11]:
        raise ValueError(
            f"HORUS catalog must have 10 or 11 columns, got {horus_catalog.shape[1]}"
        )

    # Use only first 10 columns
    catalog_10col = horus_catalog[:, :10]

    # Create dictionary for savemat
    mat_dict = {variable_name: catalog_10col}

    # Save to MAT file
    if matlab_compatible:
        # Use format 5 for maximum compatibility
        sio.savemat(output_file, mat_dict, format='5', do_compression=True)
    else:
        # Use default format
        sio.savemat(output_file, mat_dict, do_compression=True)

    print(f"✅ Saved {catalog_10col.shape[0]} events to {output_file}")
    print(f"   Variable name: '{variable_name}'")
    print(f"   Format: MATLAB {'v5 (compatible)' if matlab_compatible else 'default'}")
    print(f"   Shape: {catalog_10col.shape}")


def from_mat(file_path, variable_name='HORUS'):
    """
    Read HORUS catalog from MATLAB .mat file.

    Args:
        file_path: Path to .mat file
        variable_name: Variable name in MAT file (default 'HORUS')
                      If None, auto-detect first non-metadata variable

    Returns:
        np.ndarray: HORUS format catalog (N x 10 or N x 11)

    Examples:
        >>> cat = from_mat('data/HORUS_Italy_filtered.mat')
        >>> print(cat.shape)  # (N, 10)

    Raises:
        ValueError: If file cannot be read or variable not found

    .. note::
       This function can read existing EEPAS .mat files from the data/ directory.
    """
    import scipy.io as sio

    try:
        mat = sio.loadmat(file_path)

        # Auto-detect variable name if not specified
        if variable_name is None:
            # Find first non-metadata key
            keys = [k for k in mat.keys() if not k.startswith('__')]
            if not keys:
                raise ValueError(f"No data variables found in {file_path}")
            variable_name = keys[0]
            print(f"  Auto-detected variable: '{variable_name}'")

        # Extract catalog
        if variable_name not in mat:
            available = [k for k in mat.keys() if not k.startswith('__')]
            raise ValueError(
                f"Variable '{variable_name}' not found in {file_path}. "
                f"Available variables: {available}"
            )

        horus = mat[variable_name]

        # Validate shape
        if len(horus.shape) != 2:
            raise ValueError(
                f"Expected 2D array, got shape {horus.shape}"
            )

        if horus.shape[1] not in [10, 11]:
            raise ValueError(
                f"Expected 10 or 11 columns, got {horus.shape[1]}"
            )

        print(f"✅ Loaded MAT catalog: {horus.shape[0]} events from {file_path}")
        print(f"   Variable: '{variable_name}'")
        return horus

    except Exception as e:
        raise ValueError(f"Failed to read MAT file {file_path}: {e}")
