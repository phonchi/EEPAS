# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyEEPAS'
copyright = '2025, PyEEPAS Development Team'
author = 'PyEEPAS Development Team'
release = '0.5.0'
version = '0.5.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',        # Auto-generate API docs from docstrings
    'sphinx.ext.napoleon',       # Support Google/NumPy style docstrings
    'sphinx.ext.viewcode',       # Add links to source code
    'sphinx.ext.mathjax',        # Render mathematical equations
    'sphinx.ext.intersphinx',    # Link to other projects (NumPy, SciPy)
    'sphinx.ext.autosummary',    # Generate summary tables
    'sphinx.ext.todo',           # TODO items
    'sphinx.ext.coverage',       # Documentation coverage
    'nbsphinx',                  # Jupyter notebook integration
]

templates_path = ['_templates']
html_static_path = ['_static']
exclude_patterns = []

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Autosummary settings
autosummary_generate = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# -- nbsphinx settings -------------------------------------------------------
# Do not execute notebooks during build (they already contain outputs)
nbsphinx_execute = 'never'

# Allow notebooks with errors to be included
nbsphinx_allow_errors = True

# Kernel name for notebooks
nbsphinx_kernel_name = 'python3'

# Timeout for notebook execution (in seconds)
nbsphinx_timeout = 600

# Custom notebook CSS
nbsphinx_prolog = """
.. raw:: html

    <style>
        .nbinput .prompt,
        .nboutput .prompt {
            display: none;
        }
    </style>
"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'

html_theme_options = {
    'repository_url': 'https://github.com/your-org/EEPAS_Taiwan',
    'use_repository_button': False,
    'use_issues_button': False,
    'use_edit_page_button': False,
    'use_download_button': True,
    'navigation_with_keys': True,
    'show_toc_level': 2,
    'show_navbar_depth': 2,
}

# html_context = {
#     'display_github': True,
#     'github_user': 'your-github-username',
#     'github_repo': 'EEPAS_Taiwan',
#     'github_version': 'master',
#     'conf_py_path': '/src/python_src/docs/source/',
# }

html_logo = '_static/logo.png'
html_favicon = '_static/logo.png'

# Add any paths that contain custom static files (such as style sheets)
html_css_files = [
    'custom.css',
]

# -- Options for LaTeX output ------------------------------------------------
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
}

# Grouping the document tree into LaTeX files
latex_documents = [
    ('index', 'PyEEPAS.tex', 'PyEEPAS Documentation',
     'PyEEPAS Development Team', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    ('index', 'pyeepas', 'PyEEPAS Documentation',
     [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    ('index', 'PyEEPAS', 'PyEEPAS Documentation',
     author, 'PyEEPAS', 'Bridging the medium-term gap in open-source statistical earthquake forecasting.',
     'Miscellaneous'),
]

# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True
