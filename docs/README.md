# Documentation Directory

This directory contains the Sphinx documentation for the EEPAS project.

## 📚 Documentation Structure

```
docs/
├── source/              # Sphinx source files (.rst, configuration)
│   ├── conf.py         # Sphinx configuration
│   ├── index.rst       # Documentation homepage
│   ├── api_reference/  # API documentation (auto-generated from docstrings)
│   ├── user_guide/     # User guides and tutorials
│   ├── technical/      # Technical documentation
│   ├── examples/       # Jupyter notebook examples
│   ├── _static/        # Static assets (CSS, images, logos)
│   └── _templates/     # Custom HTML templates
│
└── build/              # Generated HTML documentation
    └── html/           # HTML output (can be served as website)
        └── index.html  # Documentation entry point
```

## 🔨 Building Documentation

### Prerequisites

Install Sphinx and required extensions:
```bash
pip install sphinx sphinx-rtd-theme nbsphinx sphinx-autodoc-typehints
```

### Build HTML Documentation

From the `python_src/` directory:

```bash
# Clean previous build
cd docs
make clean

# Build HTML documentation
make html
```

Or use `sphinx-build` directly:
```bash
sphinx-build -b html docs/source docs/build/html
```

### View Documentation

After building, open in browser:
```bash
# Linux/Mac
open docs/build/html/index.html

# Or using Python HTTP server
cd docs/build/html
python3 -m http.server 8000
# Visit http://localhost:8000
```

## 📝 Updating Documentation

### Update API Documentation

API documentation is auto-generated from Python docstrings. To update:

1. Edit docstrings in Python source files
2. Rebuild documentation:
   ```bash
   cd docs
   make clean
   make html
   ```

### Add New Modules

To document new Python modules:

1. Add module to appropriate `.rst` file in `docs/source/api_reference/`:
   ```rst
   .. automodule:: module_name
      :members:
      :undoc-members:
      :show-inheritance:
   ```

2. Rebuild documentation

### Add Jupyter Notebooks

To include new Jupyter notebooks as examples:

1. Place notebook in `analysis/` directory
2. Create symbolic link in `docs/source/examples/`:
   ```bash
   cd docs/source/examples
   ln -s ../../../analysis/your_notebook.ipynb .
   ```

3. Add to `docs/source/examples/index.rst`:
   ```rst
   .. toctree::
      :maxdepth: 1

      your_notebook
   ```

4. Rebuild documentation

## 🎨 Customization

### Theme Configuration

Current theme: **Read the Docs** (`sphinx_rtd_theme`)

To customize theme, edit `docs/source/conf.py`:
```python
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
}
```

### Logo and Branding

Project logo is configured in `docs/source/conf.py`:
```python
html_logo = '_static/logo.png'
```

To update logo, replace `docs/source/_static/logo.png`

### Custom CSS

Add custom CSS in `docs/source/_static/custom.css` and reference in `conf.py`:
```python
html_static_path = ['_static']
html_css_files = ['custom.css']
```

## 🔧 Troubleshooting

### Build Warnings

Common warnings and fixes:

**Warning: "document isn't included in any toctree"**
- Add the document to a `.. toctree::` directive in a parent document

**Warning: "undefined label"**
- Ensure referenced labels are defined with `.. _label_name:`

**Warning: "duplicate object description"**
- Remove duplicate `.. automodule::` or `.. autofunction::` directives

### Module Import Errors

If Sphinx cannot import modules:

1. Ensure modules are in Python path:
   ```python
   # In docs/source/conf.py
   import sys
   import os
   sys.path.insert(0, os.path.abspath('../..'))
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Notebook Rendering Issues

If Jupyter notebooks don't render:

1. Ensure `nbsphinx` is installed:
   ```bash
   pip install nbsphinx
   ```

2. Add to `docs/source/conf.py`:
   ```python
   extensions = [
       'nbsphinx',
       # other extensions...
   ]
   ```

## 📖 Documentation Standards

### Docstring Format

Use NumPy-style docstrings:

```python
def function_name(param1, param2):
    """
    Brief description of function.

    Extended description with more details about what the
    function does and how to use it.

    Parameters
    ----------
    param1 : type
        Description of param1
    param2 : type
        Description of param2

    Returns
    -------
    type
        Description of return value

    Examples
    --------
    >>> function_name(1, 2)
    3
    """
    return param1 + param2
```

### Section Organization

Documentation is organized into:

1. **User Guide**: Installation, quickstart, workflows
2. **API Reference**: Detailed function/class documentation
3. **Technical**: Implementation details, algorithms
4. **Examples**: Jupyter notebooks with real data

## 🚀 Deployment

### GitHub Pages

To deploy documentation to GitHub Pages:

1. Build HTML documentation:
   ```bash
   cd docs
   make html
   ```

2. Push `docs/build/html/` to GitHub repository

3. Configure GitHub Pages:
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `master` / Directory: `/docs/build/html`

Documentation will be available at:
`https://YOUR_USERNAME.github.io/EEPAS/`

### Alternative: Sphinx Build on Push

Use GitHub Actions to build Sphinx automatically:

1. Create `.github/workflows/docs.yml`:
   ```yaml
   name: Build Documentation

   on: [push]

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - uses: actions/setup-python@v2
         - run: pip install sphinx sphinx-rtd-theme nbsphinx
         - run: cd docs && make html
   ```

---

**Last Updated**: 2025-12-07
**Maintainer**: EEPAS Development Team
