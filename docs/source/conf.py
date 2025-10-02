import os
import sys
import django

# 1. Add your project root (where manage.py lives) to Python path
sys.path.insert(0, os.path.abspath('../../'))  # adjust relative to conf.py

# 2. Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'testpas.settings'

# 3. Initialize Django
django.setup()

# 4. Sphinx basic configuration
project = 'PAS-Intervention'
author = 'Your Name'
release = '1.0'

# 5. HTML theme
html_theme = 'sphinx_rtd_theme'

# 6. Extensions (optional, but recommended)
extensions = [
    'sphinx.ext.autodoc',            # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',           # Support Google and NumPy style docstrings
    'sphinx_autodoc_typehints',      # Show type hints in docs
]
