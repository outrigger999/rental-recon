# Rental Recon App

A FastAPI-based property rental analysis tool that helps evaluate rental properties by calculating commute times to work locations using Google Maps API integration.

## 🏠 Features

- **Property Management**: Add, edit, and manage rental properties with photos
- **Travel Time Analysis**: Calculate commute times using Google Maps Distance Matrix API
- **Interactive UI**: Responsive web interface with property comparison
- **Backup System**: Database backup and restore functionality
- **Pi Deployment**: Automated deployment to Raspberry Pi with systemd service
- **API Integration**: RESTful API with FastAPI framework

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google Maps API key:
   # GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

3. **Run the application:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the app:** http://localhost:8000

### Raspberry Pi Deployment

1. **Use the sync script:**
   ```bash
   ./sync_to_pi.sh
   ```

2. **Manual setup on Pi:**
   - Create `.env` file with Google Maps API key
   - Service runs automatically via systemd
   - Access at: http://192.168.10.10:8000

## 🛠 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Python 3.10
- **Frontend**: Jinja2 templates, Bootstrap, JavaScript
- **Database**: SQLite
- **APIs**: Google Maps Distance Matrix API
- **Deployment**: Raspberry Pi, systemd, conda environment

## 📁 Project Structure

```
rental_recon/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── static/              # CSS, JS, images
│   └── templates/           # Jinja2 HTML templates
├── sync_to_pi.sh           # Pi deployment script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 API Endpoints

### Web Pages
- `GET /` - Home page
- `GET /properties` - Property list
- `GET /properties/{id}` - Property details
- `GET /backup` - Backup management

### API Routes
- `GET /api/properties/` - List all properties
- `POST /api/properties/` - Create new property
- `GET /api/properties/{id}` - Get property details
- `PUT /api/properties/{id}` - Update property
- `DELETE /api/properties/{id}` - Delete property
- `POST /api/properties/{id}/calculate-travel-times` - Calculate travel times

## 🗄 Database Schema

### Properties Table
- `id`: Primary key
- `address`: Property address
- `rent`: Monthly rent amount
- `property_type`: Type of property
- `bedrooms`, `bathrooms`: Property details
- `travel_time_*`: Commute times for different time slots
- `notes`: Additional notes
- `contact_info`: Contact details

## 🔑 Environment Variables

```bash
# Required
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Optional
DATABASE_URL=sqlite:///./data/rental_recon.db
```

## 🚀 Deployment

### Raspberry Pi Setup

1. **Prerequisites:**
   - Raspberry Pi with SSH access
   - Conda environment: `rental-recon` (Python 3.10)
   - Directory: `~/rental-recon/`

2. **Deployment:**
   ```bash
   ./sync_to_pi.sh                    # Normal deployment
   ./sync_to_pi.sh --dry-run         # Preview changes
   ./sync_to_pi.sh --conda           # Update conda environment
   ```

3. **Service Management:**
   ```bash
   sudo systemctl status rental-recon.service
   sudo systemctl restart rental-recon.service
   sudo journalctl -u rental-recon.service -f
   ```

## 🔄 Git Workflow

```bash
# For new features/fixes
git checkout -b feature/new-feature
# Make changes...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# Merge to main
git checkout main
git merge feature/new-feature
git push origin main
```

## 🐛 Troubleshooting

### Common Issues

1. **Google Maps API not working:**
   - Verify API key in `.env` file
   - Check API quotas and billing in Google Cloud Console
   - Ensure Distance Matrix API is enabled

2. **Pi deployment fails:**
   - Check SSH connectivity: `ssh movingdb`
   - Verify conda environment exists
   - Check service logs: `sudo journalctl -u rental-recon.service`

3. **Database issues:**
   - Check file permissions in `data/` directory
   - Verify SQLite database file exists
   - Run backup/restore if needed

## 📝 Development Notes

- **Current Version**: Stable deployment (Initial commit: b11b705)
- **Python Version**: 3.10
- **Database**: SQLite with SQLAlchemy ORM
- **Security**: API keys excluded from git via `.gitignore`
- **Testing**: Basic API tests in `tests/` directory

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Test on Pi using sync script
4. Commit and push to GitHub
5. Create pull request

---

**Repository**: https://github.com/outrigger999/rental-recon
**Deployment**: Raspberry Pi (192.168.10.10:8000)
  - `models/` - SQLAlchemy models
  - `routers/` - FastAPI routers
  - `schemas/` - Pydantic schemas
  - `static/` - Static files (CSS, JS, etc.)
  - `templates/` - Jinja2 templates
- `data/` - SQLite database files
