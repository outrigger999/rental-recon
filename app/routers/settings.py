from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.settings import Settings
from ..schemas.settings import Settings as SettingsSchema, SettingsUpdate

router = APIRouter()

@router.get("/", response_model=SettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    """Get global settings including origin address"""
    # Get the first settings record or create one if it doesn't exist
    settings = db.query(Settings).first()
    if settings is None:
        settings = Settings(origin_address="")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.get("/origin", response_model=SettingsSchema)
def get_origin_address(db: Session = Depends(get_db)):
    """Get origin address setting (convenience endpoint)"""
    # Get the first settings record or create one if it doesn't exist
    settings = db.query(Settings).first()
    if settings is None:
        settings = Settings(origin_address="")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/", response_model=SettingsSchema)
def update_settings(origin_address: str = Form(...), db: Session = Depends(get_db)):
    """Update global settings"""
    settings = db.query(Settings).first()
    if settings is None:
        settings = Settings(origin_address=origin_address)
        db.add(settings)
    else:
        settings.origin_address = origin_address
    db.commit()
    db.refresh(settings)
    return settings
