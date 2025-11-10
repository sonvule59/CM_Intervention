from __future__ import absolute_import, unicode_literals
import os
import ssl
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testpas.settings')

# Create Celery app instance
app = Celery('config')

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Load configuration from Django settings (e.g., CELERY_BROKER_URL)
# This will set broker_url and result_backend if they're in settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Get Redis URL from environment (Render uses REDIS_URL, fallback to CELERY_BROKER_URL)
# Priority: REDIS_URL env var > CELERY_BROKER_URL env var > settings.CELERY_BROKER_URL
redis_url = os.environ.get('REDIS_URL') or os.environ.get('CELERY_BROKER_URL') or app.conf.broker_url

# Override with environment variable if it exists (Render uses REDIS_URL)
if redis_url:
    # Configure SSL for rediss:// connections BEFORE setting broker_url
    # This ensures SSL options are applied when the connection is established
    if redis_url.startswith('rediss://'):
        # For Render Redis, we need to disable SSL certificate verification
        # since Render provides Redis with self-signed certificates
        # Configure SSL options for kombu (Redis transport)
        # For Render Redis with self-signed certificates, we disable certificate verification
        app.conf.broker_transport_options = {
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_ca_certs': None,
            'ssl_certfile': None,
            'ssl_keyfile': None,
        }
        # Also set broker_use_ssl for compatibility
        app.conf.broker_use_ssl = {
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_ca_certs': None,
            'ssl_certfile': None,
            'ssl_keyfile': None,
        }
    
    # Set broker URL after SSL configuration
    app.conf.broker_url = redis_url
    
    # Only set result_backend if it's not explicitly set to None in settings
    # For Celery Beat, result backend is optional but useful for task tracking
    if app.conf.result_backend is not None:
        app.conf.result_backend = redis_url
        # Configure result backend SSL if using rediss://
        if redis_url.startswith('rediss://'):
            app.conf.redis_backend_use_ssl = {
                'ssl_cert_reqs': ssl.CERT_NONE,
                'ssl_ca_certs': None,
                'ssl_certfile': None,
                'ssl_keyfile': None,
            }
    # # Also set broker transport options for compatibility
    #     app.conf.broker_transport_options = {
    #         'ssl_cert_reqs': ssl.CERT_NONE,
    #     }
    # Connection settings for better reliability
    app.conf.broker_connection_retry = True
    app.conf.broker_connection_max_retries = 10

# Auto-discover tasks in installed apps (e.g., testpas.tasks)
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'run-daily-timeline-checks': {
        'task': 'testpas.tasks.run_daily_timeline_checks',
        'schedule': 10.0,  # Run every 10 seconds for time compression testing
    },
}

# import os
# import django
# from celery import Celery
# import ssl
# from testpas import settings
 
# # Set default Django settings module
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testpas.settings')
# django.setup()
 
# # Create Celery app
# app = Celery('config')
 
# # Read broker URL from environment variable
# REDIS_URL = os.environ.get("REDIS_URL")
# if not REDIS_URL:
#     raise ValueError("REDIS_URL environment variable not set!")
 
# # Configure broker and result backend
# app.conf.broker_url = REDIS_URL
# app.conf.result_backend = REDIS_URL
 
# # Explicit SSL context for rediss:// connections
# ssl_context = ssl.create_default_context()
# app.conf.broker_transport_options = {"ssl": ssl_context}
 
# # Load additional config from Django settings
# app.config_from_object('django.conf:settings', namespace='CELERY')
 
# # Auto-discover tasks from installed apps
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, related_name='tasks')
# app.conf.broker_use_ssl = {
#     'ssl_cert_reqs': False  # Upstash SSL without local certs
# } 
# # Optional debug task
# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
 
# # Configure Celery Beat schedule
# app.conf.beat_schedule = {
#     'run-daily-timeline-checks': {
#         'task': 'testpas.tasks.run_daily_timeline_checks',
#         'schedule': 10.0,  # For testing, adjust as needed
#     },
# }