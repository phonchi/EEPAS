"""
Path Management Tool - Unified File Path Generation
Generates standardized file paths based on configuration file and time parameters
"""

import os


def get_paths(cfg, learn_start=None, learn_end=None, fore_start=None, fore_end=None, config_file=None):
    """
    Generate standardized file paths.

    Args:
        cfg: Configuration dictionary
        learn_start: Learning start year
        learn_end: Learning end year
        fore_start: Forecast start year
        fore_end: Forecast end year
        config_file: Configuration file path (for resolving relative paths)

    Returns:
        dict: Dictionary containing various file paths (dataPath, resultsPath, eepasParam, ppeParam, etc.)
    """
    if learn_start is None:
        learn_start = cfg['learnStartYear']
    if learn_end is None:
        learn_end = cfg['learnEndYear']
    if fore_start is None:
        fore_start = cfg['forecastStartYear']
    if fore_end is None:
        fore_end = cfg['forecastEndYear']

    # Handle resultsDir relative path (use current working directory as base)
    results_dir = cfg['resultsDir']
    if not os.path.isabs(results_dir):
        # Use current working directory so all programs executed from same directory have consistent paths
        results_dir = os.path.abspath(results_dir)

    paths = {
        'dataPath': cfg['dataDir'],
        'resultsPath': results_dir
    }

    # EEPAS parameter file
    if 'outputFiles' in cfg and 'EEPASParamPattern' in cfg['outputFiles']:
        paths['eepasParam'] = os.path.join(
            paths['resultsPath'],
            cfg['outputFiles']['EEPASParamPattern'] % (learn_start, learn_end)
        )
    elif 'EEPASParamPattern' in cfg:
        paths['eepasParam'] = os.path.join(
            paths['resultsPath'],
            cfg['EEPASParamPattern'] % (learn_start, learn_end)
        )
    elif 'EEPASParamFile' in cfg:
        paths['eepasParam'] = os.path.join(paths['resultsPath'], cfg['EEPASParamFile'])
    else:
        paths['eepasParam'] = ''

    # PPE parameter file
    if 'outputFiles' in cfg and 'PPEParamPattern' in cfg['outputFiles']:
        paths['ppeParam'] = os.path.join(
            paths['resultsPath'],
            cfg['outputFiles']['PPEParamPattern'] % (learn_start, learn_end)
        )
    elif 'PPEParamPattern' in cfg:
        paths['ppeParam'] = os.path.join(
            paths['resultsPath'],
            cfg['PPEParamPattern'] % (learn_start, learn_end)
        )
    elif 'PPEParamFile' in cfg:
        paths['ppeParam'] = os.path.join(paths['resultsPath'], cfg['PPEParamFile'])
    else:
        paths['ppeParam'] = ''

    # EEPAS forecast file
    if 'outputFiles' in cfg and 'EEPASForecastPattern' in cfg['outputFiles']:
        paths['eepasOut'] = os.path.join(
            paths['resultsPath'],
            cfg['outputFiles']['EEPASForecastPattern'] % (fore_start, fore_end)
        )
    elif 'EEPASForecastPattern' in cfg:
        paths['eepasOut'] = os.path.join(
            paths['resultsPath'],
            cfg['EEPASForecastPattern'] % (fore_start, fore_end)
        )
    elif 'EEPASForecastFile' in cfg:
        paths['eepasOut'] = os.path.join(paths['resultsPath'], cfg['EEPASForecastFile'])
    else:
        paths['eepasOut'] = ''

    # PPE forecast file
    if 'outputFiles' in cfg and 'PPEForecastPattern' in cfg['outputFiles']:
        paths['ppeOut'] = os.path.join(
            paths['resultsPath'],
            cfg['outputFiles']['PPEForecastPattern'] % (fore_start, fore_end)
        )
    elif 'PPEForecastPattern' in cfg:
        paths['ppeOut'] = os.path.join(
            paths['resultsPath'],
            cfg['PPEForecastPattern'] % (fore_start, fore_end)
        )
    elif 'PPEForecastFile' in cfg:
        paths['ppeOut'] = os.path.join(paths['resultsPath'], cfg['PPEForecastFile'])
    else:
        paths['ppeOut'] = ''

    return paths
