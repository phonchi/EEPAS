#!/usr/bin/env python3
"""
Archive EEPAS Execution Results

Save configuration files and execution logs to results directory after workflow completion.
"""

import os
import sys
import argparse
from utils.result_archiver import save_execution_info, create_reproducibility_readme


def archive_workflow_results(config_path, results_dir, workflow_description, log_files, cli_args):
    """
    Archive results from a complete EEPAS workflow execution.

    Args:
        config_path: Path to configuration file
        results_dir: Results directory path
        workflow_description: Description of the workflow (e.g., "5-step EEPAS workflow")
        log_files: List of log file paths
        cli_args: Dictionary of command-line arguments used
    """
    print("\n" + "="*80)
    print("📦 Archiving Execution Results")
    print("="*80)
    print(f"Config:      {config_path}")
    print(f"Results Dir: {results_dir}")
    print(f"Workflow:    {workflow_description}")
    print("="*80 + "\n")

    # Combine all log files
    combined_log = ""
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📝 Reading log: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                combined_log += f"{'='*80}\n"
                combined_log += f"Log File: {log_file}\n"
                combined_log += f"{'='*80}\n\n"
                combined_log += f.read()
                combined_log += f"\n\n"
        else:
            print(f"⚠️  Log file not found: {log_file}")

    # Save execution info
    save_execution_info(
        config_path=config_path,
        results_dir=results_dir,
        script_name=workflow_description,
        cli_args=cli_args,
        log_content=combined_log if combined_log else None
    )

    # Create reproducibility README
    create_reproducibility_readme(results_dir)

    print("\n" + "="*80)
    print("✅ Archiving Complete!")
    print("="*80)
    print(f"📄 Config:   {os.path.join(results_dir, 'config_used.json')}")
    print(f"📋 Info:     {os.path.join(results_dir, 'execution_info.txt')}")
    print(f"📝 Log:      {os.path.join(results_dir, 'execution.log')}")
    print(f"📖 README:   {os.path.join(results_dir, 'README_REPRODUCE.md')}")
    print("="*80 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Archive EEPAS workflow execution results'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Configuration file path'
    )
    parser.add_argument(
        '--results-dir',
        required=True,
        help='Results directory path'
    )
    parser.add_argument(
        '--workflow',
        default='EEPAS 5-step workflow',
        help='Workflow description'
    )
    parser.add_argument(
        '--logs',
        nargs='+',
        required=True,
        help='List of log files to archive'
    )
    parser.add_argument(
        '--ppe-ref-mag',
        default='mT',
        help='PPE reference magnitude used'
    )
    parser.add_argument(
        '--target-mag',
        default='mT',
        help='Target magnitude threshold used (for aftershock fitting)'
    )
    parser.add_argument(
        '--three-stage',
        action='store_true',
        help='Three-stage optimization was used'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=3,
        help='Maximum boundary adjustment rounds'
    )

    args = parser.parse_args()

    # Build CLI arguments dictionary
    cli_args = {
        'ppe_ref_mag': args.ppe_ref_mag,
        'target_mag': args.target_mag,
        'three_stage': args.three_stage,
        'max_rounds': args.max_rounds,
    }

    # Archive results
    archive_workflow_results(
        config_path=args.config,
        results_dir=args.results_dir,
        workflow_description=args.workflow,
        log_files=args.logs,
        cli_args=cli_args
    )
