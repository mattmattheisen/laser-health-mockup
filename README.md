# laser-health-mockup
LaserLine Diagnostics Solutions 
# Laser Health Mockup — Single-File App

Run the dashboard and API in one Python file.

## Install
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

## Run
python laser_health_mockup.py
# or
uvicorn laser_health_mockup:app --reload --port 8000

## Open in browser:
http://localhost:8000
