# Confident Moves Intervention 

A Django-based web application for managing a research study on physical activity interventions. This system handles participant enrollment, eligibility screening, randomization, survey distribution, and physical activity monitoring across multiple waves.

## Quick Start for Front-End Developers/Designers

**Goal**: Get the UI running locally so you can edit HTML/CSS without backend complexity.

### One-Time Setup (5 minutes)

1) **Clone and setup**
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
python3 -m venv .venv

# Activate environment:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat

pip install -r requirements.txt
```

2) **Quick database setup**
```bash
# Create a simple .env file
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env
echo "DEBUG=True" >> .env
echo "ALLOWED_HOSTS=127.0.0.1,localhost" >> .env

# Setup database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Create admin user (any username/password)
```

3) **Start the server**
```bash
python manage.py runserver
```
Visit http://127.0.0.1:8000

### Daily Workflow

```bash
# Activate environment (choose your platform):
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat

# Start server
python manage.py runserver
```

### What You Can Edit

- **HTML Templates**: `templates/` folder
- **CSS/JS**: `static/` folder  
- **Images**: `static/` folder

Changes auto-reload in DEBUG mode - just refresh your browser!

### Designer Notes

- **No backend knowledge needed** - just edit HTML/CSS
- **No email setup required** - everything works locally
- **No database complexity** - SQLite handles everything automatically
- **Focus on UI** - templates and static files are your playground

### If Something Breaks

```bash
# Reset everything
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

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