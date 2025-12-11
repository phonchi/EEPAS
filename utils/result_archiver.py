#!/usr/bin/env python3
"""
Result Archiver Module

Save configuration files and execution logs to results directory for reproducibility.
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path


def save_execution_info(
    config_path: str,
    results_dir: str,
    script_name: str,
    cli_args: dict = None,
    log_content: str = None
):
    """
    Save execution information to results directory.

    Saves:
    - config_used.json: Configuration file used during execution
    - execution_info.txt: Complete execution details (time, command, parameters, etc.)
    - execution.log: Execution log (if provided)

    Args:
        config_path: Path to configuration file
        results_dir: Results directory path (e.g., results_italy/)
        script_name: Name of executed script (e.g., eepas_learning.py)
        cli_args: Command-line arguments dictionary (optional)
        log_content: Execution log content (optional)
    """
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)

    # 1. Copy configuration file
    config_dest = os.path.join(results_dir, 'config_used.json')
    try:
        shutil.copy2(config_path, config_dest)
        print(f'📄 Configuration saved to: {config_dest}')
    except Exception as e:
        print(f'⚠️  Failed to copy config: {e}')

    # 2. Generate execution info
    execution_info = []
    execution_info.append('='*80)
    execution_info.append('EEPAS Execution Information')
    execution_info.append('='*80)
    execution_info.append(f'Execution Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    execution_info.append(f'Script Name: {script_name}')
    execution_info.append(f'Config File: {config_path}')
    execution_info.append(f'Results Directory: {results_dir}')
    execution_info.append('')

    # Add configuration content
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        execution_info.append('-'*80)
        execution_info.append('Configuration Content:')
        execution_info.append('-'*80)
        execution_info.append(json.dumps(cfg, indent=2, ensure_ascii=False))
        execution_info.append('')
    except Exception as e:
        execution_info.append(f'⚠️  Failed to read config: {e}')
        execution_info.append('')

    # Add command-line arguments
    if cli_args:
        execution_info.append('-'*80)
        execution_info.append('Command-Line Arguments:')
        execution_info.append('-'*80)
        for key, value in cli_args.items():
            execution_info.append(f'  --{key}: {value}')
        execution_info.append('')

    # Save execution info
    info_file = os.path.join(results_dir, 'execution_info.txt')
    try:
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(execution_info))
        print(f'📋 Execution info saved to: {info_file}')
    except Exception as e:
        print(f'⚠️  Failed to save execution info: {e}')

    # 3. Save execution log (if provided)
    if log_content:
        log_file = os.path.join(results_dir, 'execution.log')
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)
            print(f'📝 Execution log saved to: {log_file}')
        except Exception as e:
            print(f'⚠️  Failed to save log: {e}')


def create_reproducibility_readme(results_dir: str):
    """
    Create README in results directory explaining how to reproduce results.

    Args:
        results_dir: Results directory path
    """
    readme_content = """# Result Reproducibility Guide

## 📂 Directory Contents

- `config_used.json`: Complete configuration file used during execution
- `execution_info.txt`: Detailed execution information (time, parameters, etc.)
- `execution.log`: Complete execution log (if available)
- `Fitted_par_*.csv`: Learned parameter results
- `PREVISIONI_*.mat`: Forecast results (if available)

## 🔄 How to Reproduce These Results

### Method 1: Use Saved Configuration

```bash
# Reproduce results using saved configuration
python3 eepas_learning_auto_boundary.py --config {results_dir}/config_used.json
```

### Method 2: Check Execution Info

Review `execution_info.txt` for complete execution parameters, then run the same command.

## 📋 Checklist

When reproducing results, ensure:
- ✅ Same Python version
- ✅ Same data files (data/*.mat)
- ✅ Same configuration file (config_used.json)
- ✅ Same command-line arguments (see execution_info.txt)

## ⚠️ Important Notes

- Optimizer may produce slightly different results due to floating-point precision
- With `--multi-start`, different runs may select different best starting points
- Ensure correct data file paths (if directory was moved)
"""

    readme_file = os.path.join(results_dir, 'README_REPRODUCE.md')
    try:
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content.format(results_dir=results_dir))
        print(f'📖 Reproducibility guide saved to: {readme_file}')
    except Exception as e:
        print(f'⚠️  Failed to save README: {e}')
