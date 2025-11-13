# Start the Django web app
web: gunicorn config.wsgi --log-file -

# Run migrations before each deploy
release: python manage.py migrate

# Start the Celery worker
worker: celery -A testpas.celery worker --loglevel=info

# Start Celery Beat for scheduled tasks
beat: celery -A testpas.celery beat --loglevel=info
