#!/usr/bin/env python3
"""
PyCSEP Shapely 2.x Compatibility Patch

This module patches pycsep.core.regions to fix compatibility issues with Shapely 2.x.
The patch replaces deprecated `boundary.xy` with `envelope.boundary.coords.xy`.

Usage:
    python patch_pycsep.py

Note:
    This patch is only needed for pycsep versions that haven't been updated
    for Shapely 2.x compatibility.
"""

import os
import csep


def patch_csep_regions():
    """
    Patch pycsep.core.regions for Shapely 2.x compatibility.

    Automatically locates the pycsep installation and replaces deprecated
    Shapely API calls with compatible versions.

    Changes:
        - Old: `joined_poly.boundary.xy`
        - New: `joined_poly.envelope.boundary.coords.xy`

    Returns:
        None: Prints status message and modifies pycsep installation file

    Raises:
        Exception: If file cannot be read or written (permission issues)
    """
    # Automatically locate the installation path of the pycsep package
    package_dir = os.path.dirname(csep.__file__)
    target_file = os.path.join(package_dir, 'core', 'regions.py')
    
    print(f"Checking file: {target_file}")
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Define the old code to replace and the new code
        old_code = "joined_poly.boundary.xy"
        new_code = "joined_poly.envelope.boundary.coords.xy"
        
        if old_code in content:
            new_content = content.replace(old_code, new_code)
            
            # Write back to the file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ Success: Code has been automatically replaced.")
        elif new_code in content:
            print("ℹ️ Skipped: Code has already been modified.")
        else:
            print(f"⚠️ Warning: Target string '{old_code}' not found. The version might have changed or the code structure differs.")
            
    except Exception as e:
        print(f"❌ Error: Unable to modify file. Please verify you have write permissions.\nDetail: {e}")

if __name__ == "__main__":
    patch_csep_regions()