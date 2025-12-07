#!/bin/bash
# Batch cleanup all module docstrings

cd /home/math/EEPAS_Taiwan-main/src/python_src

# eepas_likelihood.py
python3 << 'EOF'
import re

files = {
    'eepas_likelihood.py': '''"""
EEPAS Likelihood Calculation

Calculate negative log-likelihood for EEPAS model parameter optimization.

Combines PPE background rate with precursory signals from weighted earthquakes.
"""''',

    'neg_log_like_aftershock.py': '''"""
Aftershock Model Negative Log-Likelihood

Calculate NLL for aftershock model parameter estimation (ν, κ).

Used in Step 2 to distinguish independent events from aftershocks.
"""''',

    'optimize_eepas_parameters.py': '''"""
EEPAS Parameter Optimization Engine

Three-stage optimization procedure for EEPAS model parameters:
- Stage 1: Optimize magnitude scaling (am, bm, Sm)
- Stage 2: Optimize temporal scaling (at, bt, St)
- Stage 3: Optimize spatial scaling (ba, Sa) and μ

Supports single-stage joint optimization and multiple optimizers.
"""''',

    'ppe_optimization.py': '''"""
PPE Parameter Optimization Engine

Optimize PPE model parameters (a, d, s) using Maximum Likelihood Estimation.

Called by ppe_learning.py to find optimal spatial clustering parameters.
"""''',
}

for filename, new_docstring in files.items():
    try:
        with open(filename, 'r') as f:
            content = f.read()

        # Find and replace module docstring (first """ ... """)
        pattern = r'(#!/usr/bin/env python3\n)"""[\s\S]*?"""'
        replacement = r'\1' + new_docstring

        new_content = re.sub(pattern, replacement, content, count=1)

        if new_content != content:
            with open(filename, 'w') as f:
                f.write(new_content)
            print(f"✅ {filename}")
        else:
            print(f"⏭️ {filename} (no change)")
    except Exception as e:
        print(f"❌ {filename}: {e}")
EOF

echo "Done!"
