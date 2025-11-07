# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery
# from testpas import settings
# import django
# import os
# from celery import Celery
# from celery.schedules import crontab

# # Set the default Django settings module for Celery
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testpas.settings')

# # Create Celery app instance
# app = Celery('config')

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')

# # Load configuration from Django settings (e.g., CELERY_BROKER_URL)
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Auto-discover tasks in installed apps (e.g., testpas.tasks)
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='tasks')

# # Configure Celery Beat schedule
# app.conf.beat_schedule = {
#     'run-daily-timeline-checks': {
#         'task': 'testpas.tasks.run_daily_timeline_checks',
#         'schedule': 10.0,  # Run every 10 seconds for time compression testing
#     },
# }

import os
import django
from celery import Celery
import ssl
from testpas import settings
 
# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testpas.settings')
django.setup()
 
# Create Celery app
app = Celery('config')
 
# Read broker URL from environment variable
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable not set!")
 
# Configure broker and result backend
app.conf.broker_url = REDIS_URL
app.conf.result_backend = REDIS_URL
 
# Explicit SSL context for rediss:// connections
ssl_context = ssl.create_default_context()
app.conf.broker_transport_options = {"ssl": ssl_context}
 
# Load additional config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')
 
# Auto-discover tasks from installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='tasks')
 
# Optional debug task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
 
# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'run-daily-timeline-checks': {
        'task': 'testpas.tasks.run_daily_timeline_checks',
        'schedule': 10.0,  # For testing, adjust as needed
    },
}