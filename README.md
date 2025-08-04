# Rental Recon App

A FastAPI application for capturing and organizing rental property opportunities.

## Features

- Record property details (address, type, price, square footage, etc.)
- Track amenities (cat friendly, air conditioning, on-premises parking)
- Capture and store property images
- Simple web interface for data entry
- SQLite database for data storage

## Setup

1. Create conda environment:
```
conda create -n rental_recon python=3.9
conda activate rental_recon
```

2. Install requirements:
```
pip install -r requirements.txt
```

3. Run the application:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Access the web interface at `http://localhost:8000` or the IP address of your Raspberry Pi

## Raspberry Pi Deployment

This application is designed to run on a Raspberry Pi 4 with a conda environment.

## Project Structure

- `app/` - Main application code
  - `models/` - SQLAlchemy models
  - `routers/` - FastAPI routers
  - `schemas/` - Pydantic schemas
  - `static/` - Static files (CSS, JS, etc.)
  - `templates/` - Jinja2 templates
- `data/` - SQLite database files
