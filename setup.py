#!/usr/bin/env python3
"""
EEPAS Taiwan - Python Implementation
Setup script for installation
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip()
        for line in fh
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="eepas-taiwan",
    version="1.0.0",
    author="EEPAS Taiwan Project",
    author_email="your-email@example.com",
    description="EEPAS earthquake prediction model - Python implementation for Taiwan",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/EEPAS_Taiwan",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/EEPAS_Taiwan/issues",
        "Documentation": "https://github.com/your-org/EEPAS_Taiwan/blob/master/src/python_src/README.md",
        "Source Code": "https://github.com/your-org/EEPAS_Taiwan",
    },
    packages=find_packages(include=["analysis", "utils"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "viz": [
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "eepas-learn=eepas_learning_auto_boundary:main",
            "eepas-forecast=eepas_make_forecast:main",
            "ppe-learn=ppe_learning:main",
            "ppe-forecast=ppe_make_forecast:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md"],
    },
    zip_safe=False,
    keywords=[
        "earthquake",
        "seismology",
        "prediction",
        "EEPAS",
        "Taiwan",
        "geophysics",
    ],
)
