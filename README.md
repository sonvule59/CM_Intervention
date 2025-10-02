# Confident Moves Intervention 

A Django-based web application for managing a research study on physical activity interventions. This system handles participant enrollment, eligibility screening, randomization, survey distribution, and physical activity monitoring across multiple waves.

## Local Development (for Designers)

This guide lets you run the app locally without access to production secrets. You'll use a private .env file (not committed to Git) and SQLite (no external DB needed).

### Prerequisites
- Python 3.11+ installed
- pip installed
- Optional (only if doing background jobs): Redis installed and running

### Setup Steps

1) **Clone the repo**
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

2) **Create and activate a virtual environment**
- macOS/Linux:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```bash
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

3) **Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4) **Create a local env file**
- Copy `.env.example` to `.env`
- Fill in values as shown below. Do not commit .env.

If `.env.example` doesn't exist yet, create both files like this:

**Add `.env.example` to the repo (safe to commit)**
- This is a template. Do not put secrets here.

```
# Core
SECRET_KEY=REPLACE_ME
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# App
BASE_URL=http://127.0.0.1:8000

# Timeline testing (optional)
TIME_COMPRESSION=True
SECONDS_PER_DAY=10

# Email (optional for local)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# EMAIL_HOST=smtp.example.com
# EMAIL_HOST_USER=your_user
# EMAIL_HOST_PASSWORD=your_password
# EMAIL_PORT=587
# EMAIL_USE_TLS=True

# Celery/Redis (optional)
# REDIS_URL=redis://localhost:6379/0
```

**Create your private `.env` (do NOT commit)**
- Use a real Django secret key:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- Paste into `.env`:
```
SECRET_KEY=PASTE_GENERATED_SECRET_HERE
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
BASE_URL=http://127.0.0.1:8000
TIME_COMPRESSION=True
SECONDS_PER_DAY=10
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# REDIS_URL=redis://localhost:6379/0
```

5) **Initialize the database**
```bash
python manage.py migrate
python manage.py createsuperuser
```
Optional seed content:
```bash
python manage.py seed_content
python manage.py seed_email_template
python manage.py seed_eligibility_survey
```

6) **Run the app**
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000

7) **(Optional) Run background jobs**
If you need emails or scheduled tasks locally:
```bash
# Start Redis (if using Redis)
redis-server

# Start Celery worker
celery -A config.celery worker --loglevel=INFO

# Start Celery beat
celery -A config.celery beat --loglevel=INFO
```
If you don't need automation, you can skip Celery/Beat and the app will still run for UI work.

### Designer Notes
- Most UI is under `templates/` and `static/` — you can edit HTML/CSS safely without touching backend logic.
- If you change static files, they'll reload automatically in DEBUG mode.
- Emails are printed to the console with the console backend, so no email credentials are needed.

### Security and Secrets
- Never commit `.env`. Keep it private and share via a secure channel (1Password, Bitwarden, etc.).
- `.env.example` is safe to commit and should document required variables.

### Troubleshooting
- If you hit import or migration errors, re-run:
  ```bash
  pip install -r requirements.txt
  python manage.py migrate
  ```
- If Celery complains about Redis and you don't need background tasks, just don't start Celery/Beat.

---

For technical support or questions about the system:
- **Principal Investigator**: Seungmin ("Seung") Lee
- **Email**: seunglee@iastate.edu
- **Principal Developer**: Son Vu
- **Email**: svu23@iastate.edu

## License

This project is proprietary software for research purposes. All rights reserved.

## Acknowledgments

Developed for the Obesity and Physical Activity Research Team, PAL Lab, Department of Kinesiology, Iowa State University.