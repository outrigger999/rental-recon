from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .database import engine, Base, get_db
from sqlalchemy.orm import Session
from .models import property as property_model
from .models import settings as settings_model
from .routers import property as property_router
from .routers import image as image_router
from .routers import settings as settings_router
from .routers import notes as notes_router
from .routers import admin as admin_router
from .routers import backup as backup_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="Rental Recon")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(property_router.router, prefix="/api/properties", tags=["properties"])
app.include_router(image_router.router, prefix="/api/properties", tags=["images"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(notes_router.router, prefix="/api/properties", tags=["notes"])
app.include_router(admin_router.router, prefix="/api", tags=["admin"])
app.include_router(backup_router.router, tags=["backup"])

# Create the initial image directory if it doesn't exist
os.makedirs("app/static/images", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/properties/new", response_class=HTMLResponse)
async def new_property(request: Request):
    """Render the new property form"""
    return templates.TemplateResponse("new_property.html", {"request": request})

@app.get("/properties/{property_id}", response_class=HTMLResponse)
async def view_property(request: Request, property_id: int, db: Session = Depends(get_db)):
    """Render the property detail page"""
    # Check if property exists
    property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Load environment variables from .env
    load_dotenv()
    # Get Google Maps API key from .env
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    return templates.TemplateResponse("property_detail.html", {
        "request": request,
        "property": property,
        "google_maps_api_key": google_maps_api_key
    })

@app.get("/properties/{property_id}/edit", response_class=HTMLResponse)
async def edit_property(request: Request, property_id: int, db: Session = Depends(get_db)):
    """Render the property edit form"""
    # Check if property exists
    property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return templates.TemplateResponse("edit_property.html", {
        "request": request,
        "property": property
    })

@app.get("/properties", response_class=HTMLResponse)
async def list_properties(request: Request, id: str = None, db: Session = Depends(get_db)):
    """Render the property list page or property detail page if id is provided"""
    # If id parameter is provided, render property detail page (workaround for proxy issues)
    if id is not None and id.strip():
        try:
            property_id = int(id)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid property ID")
        # Check if property exists
        property = db.query(property_model.Property).filter(property_model.Property.id == property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Load environment variables from .env
        load_dotenv()
        # Get Google Maps API key from .env
        google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        
        return templates.TemplateResponse("property_detail.html", {
            "request": request,
            "property": property,
            "google_maps_api_key": google_maps_api_key
        })
    
    # Otherwise render property list page
    return templates.TemplateResponse("property_list.html", {"request": request})
