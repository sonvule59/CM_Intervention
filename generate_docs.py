# generate_docs.py
import os
import django
import pydoc

# 1. Set your settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'testpas.settings'

# 2. Initialize Django
django.setup()

# 3. Generate HTML docs for a module
pydoc.writedoc('testpas.views')
