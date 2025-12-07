"""
DataLoader - EEPAS System Data Loading Utility Class
Provides unified configuration file loading, model parameter management, and seismic catalog reading functionality
"""

import json
import os
import scipy.io as sio
import numpy as np


class DataLoader:
    """Unified data loading utility class"""

    @staticmethod
    def load_config(config_file='config.json'):
        """
        Load system configuration from JSON config file.
        Automatically fills in missing default values to ensure backward compatibility.

        Args:
            config_file: Configuration file path

        Returns:
            dict: Configuration dictionary
        """
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f'Configuration file {config_file} not found')

        with open(config_file, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        # Fill in default values to ensure backward compatibility
        defaults = {
            'dataDir': 'data',
            'resultsDir': 'results',
            'catalogStartYear': 1991,
            'learnStartYear': 2002,
            'learnEndYear': 2016,
            'forecastStartYear': 2016,
            'forecastEndYear': 2025
        }

        for key, value in defaults.items():
            cfg.setdefault(key, value)

        # Process inputFiles
        if 'inputFiles' not in cfg:
            cfg['inputFiles'] = {}

        # Backward compatibility: support old names
        if 'horusFile' in cfg['inputFiles'] and 'catalogFile' not in cfg['inputFiles']:
            cfg['inputFiles']['catalogFile'] = cfg['inputFiles']['horusFile']
        if 'cptiFile' in cfg['inputFiles'] and 'neighborhoodRegionFile' not in cfg['inputFiles']:
            cfg['inputFiles']['neighborhoodRegionFile'] = cfg['inputFiles']['cptiFile']
        if 'celleFile' in cfg['inputFiles'] and 'testingRegionFile' not in cfg['inputFiles']:
            cfg['inputFiles']['testingRegionFile'] = cfg['inputFiles']['celleFile']

        # Set default values
        cfg['inputFiles'].setdefault('catalogFile', 'GDMScatalog_A_twd97.mat')
        cfg['inputFiles'].setdefault('neighborhoodRegionFile', 'CPTI11.mat')
        cfg['inputFiles'].setdefault('testingRegionFile', 'CELLE_ter_TW_twd97.mat')

        # Process outputFiles
        if 'outputFiles' not in cfg:
            cfg['outputFiles'] = {}
        cfg['outputFiles'].setdefault('EEPASParamPattern', 'Fitted_par_EEPAS_%d_%d.csv')
        cfg['outputFiles'].setdefault('PPEParamPattern', 'Fitted_par_PPE_%d_%d.csv')
        cfg['outputFiles'].setdefault('AftershockParamPattern', 'Fitted_par_aftershock_%d_%d.csv')
        cfg['outputFiles'].setdefault('EEPASForecastPattern', 'PREVISIONI_3m_EEPAS_%d_%d.mat')
        cfg['outputFiles'].setdefault('PPEForecastPattern', 'PREVISIONI_3m_PPE_%d_%d.mat')

        # Process optimization configuration
        if 'optimization' not in cfg:
            cfg['optimization'] = {
                'stage1': {
                    'parameters': ['am', 'at', 'Sa', 'u'],
                    'initialValues': [2.32, 0.11, 0.80, 0.20],
                    'lowerBounds': [0.5, 0.001, 0.01, 0.0],
                    'upperBounds': [4.0, 2.5, 2.0, 0.75],
                    'fixedValues': {'bm': 0.75, 'Sm': 0.23, 'bt': 0.63, 'St': 0.43, 'ba': 0.57}
                },
                'stage2': {
                    'parameters': ['Sm', 'bt', 'St', 'ba', 'u'],
                    'initialValues': [0.23, 0.63, 0.43, 0.57, 'u_from_stage1'],
                    'lowerBounds': [0.05, 0.05, 0.05, 0.05, 0.0],
                    'upperBounds': [1.0, 1.0, 1.0, 1.0, 0.75]
                },
                'stage3': {
                    'parameters': ['am', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u'],
                    'lowerBounds': [0.5, 0.05, 0.001, 0.05, 0.05, 0.05, 0.01, 0.0],
                    'upperBounds': [4.0, 1.0, 2.5, 1.0, 1.0, 1.0, 2.0, 0.75],
                    'fixedValues': {'bm': 0.75}
                }
            }

        return cfg

    @staticmethod
    def load_catalogs(input_arg):
        """
        Load seismic catalog files.

        Args:
            input_arg: Configuration file path (.json) or data directory path

        Returns:
            tuple: (HORUS, CPTI11, CELLE) three data matrices
        """
        # Determine if input is config file or data directory
        if input_arg.endswith('.json'):
            cfg = DataLoader.load_config(input_arg)
            data_path = cfg['dataDir']

            # If relative path, resolve relative to config file directory
            if not os.path.isabs(data_path):
                config_dir = os.path.dirname(os.path.abspath(input_arg))
                data_path = os.path.join(config_dir, data_path)

            catalog_file = os.path.join(data_path, cfg['inputFiles']['catalogFile'])
            neighborhood_file = os.path.join(data_path, cfg['inputFiles']['neighborhoodRegionFile'])
            testing_file = os.path.join(data_path, cfg['inputFiles']['testingRegionFile'])
        else:
            raise ValueError('Configuration file path required')

        if not os.path.isdir(data_path):
            raise FileNotFoundError(f'Data directory not found: {data_path}')

        if not os.path.isfile(catalog_file):
            raise FileNotFoundError(f'Catalog file not found: {catalog_file}')
        if not os.path.isfile(neighborhood_file):
            raise FileNotFoundError(f'Neighborhood region data file not found: {neighborhood_file}')
        if not os.path.isfile(testing_file):
            raise FileNotFoundError(f'Testing region data file not found: {testing_file}')

        # Load MATLAB .mat files
        catalog_data = sio.loadmat(catalog_file)
        neighborhood_data = sio.loadmat(neighborhood_file)
        testing_data = sio.loadmat(testing_file)

        # Auto-detect key (backward compatibility)
        # Seismic catalog file (Catalog)
        catalog_keys = [k for k in catalog_data.keys() if not k.startswith('__')]
        if len(catalog_keys) == 0:
            raise ValueError(f'No data found in catalog file: {catalog_file}')
        HORUS = catalog_data[catalog_keys[0]]

        # Neighborhood region file (could be CPTI11, CPTI15, CELLE, etc.)
        neighborhood_keys = [k for k in neighborhood_data.keys() if not k.startswith('__')]
        if len(neighborhood_keys) == 0:
            raise ValueError(f'No data found in neighborhood region file: {neighborhood_file}')
        CPTI11 = neighborhood_data[neighborhood_keys[0]]

        # Testing region file (could be CELLE, CELLESD, etc.)
        testing_keys = [k for k in testing_data.keys() if not k.startswith('__')]
        if len(testing_keys) == 0:
            raise ValueError(f'No data found in testing region file: {testing_file}')
        CELLE = testing_data[testing_keys[0]]

        return HORUS, CPTI11, CELLE

    @staticmethod
    def load_model_params(config_file='config.json'):
        """
        Load model parameters from configuration.

        Args:
            config_file: Configuration file path

        Returns:
            dict: Model parameters dictionary
        """
        cfg = DataLoader.load_config(config_file)

        # Set default values
        defaults = {
            'delay': 10,
            'B': 0.93,
            'm0': 2.35,
            'mT': 5.0,
            'delta': 1.2,
            'p': 1.09,
            'c': 0.001,
            'sigmaU': 0.006,
            'weightFlag': 0,
            'useCausalEW': 1,
            'useRollingUpdate': True,
            'forecastPeriodDays': 91.31
        }

        params = defaults.copy()

        # If config file contains modelParams field, read parameters
        if 'modelParams' in cfg:
            for key in defaults.keys():
                if key in cfg['modelParams']:
                    params[key] = cfg['modelParams'][key]

        return params

    @staticmethod
    def load_spatial_regions(config_file='config.json'):
        """
        Load spatial region definitions (supports single or dual region configurations).

        Single region configuration uses the same grid for both testing and neighborhood regions.
        Dual region configuration uses a grid for testing and a polygon for neighborhood region.

        Args:
            config_file: Configuration file path

        Returns:
            dict: Dictionary containing the following keys:

                - 'testing_region': Testing region data (numpy array)
                - 'testing_type': 'grid' or 'polygon'
                - 'neighborhood_region': Neighborhood region data (numpy array)
                - 'neighborhood_type': 'grid' or 'polygon'
                - 'config': Region configuration (if exists)
        """
        cfg = DataLoader.load_config(config_file)
        data_path = cfg['dataDir']

        # Resolve absolute path
        if not os.path.isabs(data_path):
            config_dir = os.path.dirname(os.path.abspath(config_file))
            data_path = os.path.join(config_dir, data_path)

        # Get file paths
        neighborhood_file = os.path.join(data_path, cfg['inputFiles']['neighborhoodRegionFile'])
        testing_file = os.path.join(data_path, cfg['inputFiles']['testingRegionFile'])

        if not os.path.isfile(neighborhood_file):
            raise FileNotFoundError(f'Neighborhood region data file not found: {neighborhood_file}')
        if not os.path.isfile(testing_file):
            raise FileNotFoundError(f'Testing region data file not found: {testing_file}')

        # Load testing region (always grid format)
        testing_data = sio.loadmat(testing_file)
        # Auto-find non-private keys (not starting with __)
        testing_keys = [k for k in testing_data.keys() if not k.startswith('__')]
        if len(testing_keys) == 0:
            raise ValueError(f'No data found in testing region file: {testing_file}')
        testing_key = testing_keys[0]  # Take first non-private key
        testing_region = testing_data[testing_key]

        # Load neighborhood region (could be grid or polygon)
        neighborhood_data = sio.loadmat(neighborhood_file)
        neighborhood_keys = [k for k in neighborhood_data.keys() if not k.startswith('__')]
        if len(neighborhood_keys) == 0:
            raise ValueError(f'No data found in neighborhood region file: {neighborhood_file}')
        neighborhood_key = neighborhood_keys[0]
        neighborhood_region_raw = neighborhood_data[neighborhood_key]

        # Determine region type
        # Default: testing region is always grid
        testing_type = 'grid'

        # neighborhood region type determination
        # If explicitly specified in regionConfig, use the specified value
        # Otherwise, auto-detect based on data shape
        region_config = cfg.get('regionConfig', {})
        neighborhood_type = region_config.get('neighborhoodRegionType', None)

        if neighborhood_type is None:
            # Auto-detect: if columns <= 4 and rows < 100, treat as polygon
            # Otherwise treat as grid
            n_rows, n_cols = neighborhood_region_raw.shape
            if n_cols <= 4 and n_rows < 100:
                neighborhood_type = 'polygon'
            else:
                neighborhood_type = 'grid'

        # Handle multi-column polygon data (e.g. CPTI15 has 4 columns: lat, lon, y_proj, x_proj)
        # CPTI15 format: [latitude, longitude, Y_projected, X_projected]
        # If polygon with 4 columns, use last two columns and swap order to (X, Y)
        if neighborhood_type == 'polygon' and neighborhood_region_raw.shape[1] == 4:
            # Take last two columns: [Y_projected, X_projected]
            # Swap order to: [X_projected, Y_projected]
            neighborhood_region_raw = neighborhood_region_raw[:, [3, 2]]  # X first, Y second

        # Special handling for single region mode: if Testing and Neighborhood regions are identical, use same data
        # (backward compatibility)
        if testing_key == neighborhood_key and testing_region.shape == neighborhood_region_raw.shape:
            # Possibly single region mode (same file or same data)
            if np.array_equal(testing_region, neighborhood_region_raw):
                neighborhood_region = testing_region
                neighborhood_type = 'grid'
            else:
                neighborhood_region = neighborhood_region_raw
        else:
            neighborhood_region = neighborhood_region_raw

        result = {
            'testing_region': testing_region,
            'testing_type': testing_type,
            'neighborhood_region': neighborhood_region,
            'neighborhood_type': neighborhood_type,
            'config': region_config
        }

        return result

    @staticmethod
    def load_custom_stages(config_file='config.json'):
        """
        Load custom optimization stages configuration.

        Args:
            config_file: Configuration file path

        Returns:
            dict or None: Custom stages configuration, or None if not enabled
                {
                    'enable': bool,
                    'stages': [
                        {
                            'name': str,
                            'parameters': list[str],
                            'initialValues': list[float] or None,
                            'lowerBounds': list[float],
                            'upperBounds': list[float],
                            'fixedValues': dict
                        },
                        ...
                    ]
                }
        """
        cfg = DataLoader.load_config(config_file)

        # Check if custom stages are enabled
        custom_config = cfg.get('optimization', {}).get('customStages', {})

        if not custom_config.get('enable', False):
            return None

        # Validate custom stages configuration
        if 'stages' not in custom_config:
            raise ValueError('customStages.enable is true but no stages defined')

        stages = custom_config['stages']

        if not isinstance(stages, list) or len(stages) == 0:
            raise ValueError('customStages.stages must be a non-empty list')

        # Validate each stage
        DataLoader.validate_custom_stages(stages)

        return custom_config

    @staticmethod
    def validate_custom_stages(stages):
        """
        Validate custom stages configuration.

        Checks:
        1. All parameter names are valid EEPAS parameters
        2. Bounds and initial values have correct lengths
        3. Fixed parameters + optimized parameters = 9 parameters
        4. No duplicate optimization of same parameter in same stage

        Args:
            stages: List of stage configurations

        Raises:
            ValueError: If validation fails
        """
        # Valid EEPAS parameter names
        valid_params = {'am', 'bm', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u'}

        for stage_idx, stage in enumerate(stages):
            stage_num = stage_idx + 1
            stage_name = stage.get('name', f'Stage {stage_num}')

            # Check required fields
            if 'parameters' not in stage:
                raise ValueError(f'{stage_name}: missing "parameters" field')
            if 'lowerBounds' not in stage:
                raise ValueError(f'{stage_name}: missing "lowerBounds" field')
            if 'upperBounds' not in stage:
                raise ValueError(f'{stage_name}: missing "upperBounds" field')

            parameters = stage['parameters']
            lower_bounds = stage['lowerBounds']
            upper_bounds = stage['upperBounds']
            initial_values = stage.get('initialValues', None)
            fixed_values = stage.get('fixedValues', {})

            # Check parameters are valid
            if not isinstance(parameters, list) or len(parameters) == 0:
                raise ValueError(f'{stage_name}: "parameters" must be a non-empty list')

            # Check all parameter names are valid
            for param in parameters:
                if param not in valid_params:
                    raise ValueError(f'{stage_name}: invalid parameter name "{param}". Must be one of {valid_params}')

            # Check no duplicates in parameters
            if len(parameters) != len(set(parameters)):
                raise ValueError(f'{stage_name}: duplicate parameters in optimization list')

            # Check bounds lengths match
            if len(lower_bounds) != len(parameters):
                raise ValueError(f'{stage_name}: lowerBounds length ({len(lower_bounds)}) does not match parameters length ({len(parameters)})')
            if len(upper_bounds) != len(parameters):
                raise ValueError(f'{stage_name}: upperBounds length ({len(upper_bounds)}) does not match parameters length ({len(parameters)})')

            # Check initial values length (if provided)
            if initial_values is not None and not isinstance(initial_values, str):
                if len(initial_values) != len(parameters):
                    raise ValueError(f'{stage_name}: initialValues length ({len(initial_values)}) does not match parameters length ({len(parameters)})')

            # Check fixed parameters are valid
            for param in fixed_values.keys():
                if param not in valid_params:
                    raise ValueError(f'{stage_name}: invalid fixed parameter name "{param}". Must be one of {valid_params}')

            # Check no overlap between optimized and fixed parameters
            optimized_set = set(parameters)
            fixed_set = set(fixed_values.keys())
            overlap = optimized_set & fixed_set
            if overlap:
                raise ValueError(f'{stage_name}: parameters appear in both optimization and fixed lists: {overlap}')

            # Check total parameters = 9 (optimized + fixed, other parameters will be inherited)
            # For first stage: must specify all 9 parameters
            # For later stages: can inherit from previous stages
            total_specified = optimized_set | fixed_set
            if stage_idx == 0:
                # First stage must specify all parameters
                if len(total_specified) != 9:
                    missing = valid_params - total_specified
                    raise ValueError(f'{stage_name}: First stage must specify all 9 parameters. Missing: {missing}')
            else:
                # Later stages can inherit, just check no duplicate
                # (Inheritance will be handled by optimize_custom_stages)
                pass

            print(f'✓ {stage_name} validation passed: optimizing {len(parameters)} parameters, fixing {len(fixed_values)} parameters')

    @staticmethod
    def detect_stage1_config_type(config_file='config.json'):
        """
        Detect whether stage1 configuration is for single-stage or three-stage optimization.

        Detection logic:
        - If stage1 optimizes all 8 parameters (am, Sm, at, bt, St, ba, Sa, u) → Single-stage
        - Otherwise → Three-stage (stage1 is part of three-stage optimization)

        Args:
            config_file: Configuration file path

        Returns:
            str: 'single' if stage1 is single-stage config, 'three' if it's three-stage config
        """
        cfg = DataLoader.load_config(config_file)

        # Check if stage1 exists
        if 'optimization' not in cfg or 'stage1' not in cfg['optimization']:
            raise ValueError('No stage1 configuration found in optimization section')

        stage1 = cfg['optimization']['stage1']

        # Check if stage1 has parameters field
        if 'parameters' not in stage1:
            raise ValueError('stage1 configuration missing "parameters" field')

        parameters = stage1['parameters']

        # Single-stage: optimizes all 8 parameters (bm is always fixed)
        # Expected: ['am', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u']
        single_stage_params = {'am', 'Sm', 'at', 'bt', 'St', 'ba', 'Sa', 'u'}

        if set(parameters) == single_stage_params:
            return 'single'
        else:
            return 'three'
