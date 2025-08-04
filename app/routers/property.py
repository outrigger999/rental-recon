import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.property import Property, PropertyImage
from ..models.settings import Settings
from ..schemas.property import PropertyCreate, Property as PropertySchema
from ..services.travel_time import TravelTimeService

router = APIRouter()

@router.post("/", response_model=PropertySchema)
def create_property(
    address: str = Form(...),
    property_type: str = Form(...),
    price_per_month: float = Form(...),
    square_footage: float = Form(...),
    cat_friendly: bool = Form(False),
    air_conditioning: bool = Form(False),
    on_premises_parking: bool = Form(False),
    description: Optional[str] = Form(None),
    contacts: Optional[str] = Form(None),
    main_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Create a new property listing"""
    property_data = {
        "address": address,
        "property_type": property_type,
        "price_per_month": price_per_month,
        "square_footage": square_footage,
        "cat_friendly": cat_friendly,
        "air_conditioning": air_conditioning,
        "on_premises_parking": on_premises_parking,
        "description": description,
        "contacts": contacts
    }
    
    db_property = Property(**property_data)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    
    # Handle main image upload
    if main_image and main_image.filename:
        # Create property-specific images directory
        property_image_dir = f"app/static/images/property_{db_property.id}"
        os.makedirs(property_image_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = main_image.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{property_image_dir}/{unique_filename}"
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(main_image.file, buffer)
        
        # Create PropertyImage record
        db_image = PropertyImage(
            filename=unique_filename,
            is_main=True,
            property_id=db_property.id
        )
        db.add(db_image)
        db.commit()
    
    # Auto-calculate travel times if origin address is set
    try:
        settings = db.query(Settings).first()
        if settings and settings.origin_address:
            travel_service = TravelTimeService()
            travel_times = travel_service.calculate_travel_times(
                origin=settings.origin_address,
                destination=address
            )
            
            # Update property with calculated travel times
            for time_key, time_value in travel_times.items():
                if time_value is not None:
                    setattr(db_property, time_key, time_value)
            
            db.commit()
            db.refresh(db_property)
    except Exception as e:
        # Log error but don't fail property creation
        print(f"Warning: Could not calculate travel times: {e}")
    
    return db_property


@router.get("/", response_model=List[PropertySchema])
def read_properties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all property listings"""
    properties = db.query(Property).offset(skip).limit(limit).all()
    return properties


@router.get("/{property_id}", response_model=PropertySchema)
def read_property(property_id: int, db: Session = Depends(get_db)):
    """Get a specific property by ID"""
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property


@router.put("/{property_id}", response_model=PropertySchema)
def update_property(
    property_id: int,
    address: str = Form(...),
    property_type: str = Form(...),
    price_per_month: float = Form(...),
    square_footage: float = Form(...),
    cat_friendly: bool = Form(False),
    air_conditioning: bool = Form(False),
    on_premises_parking: bool = Form(False),
    description: Optional[str] = Form(None),
    contacts: Optional[str] = Form(None),
    main_image: Optional[UploadFile] = File(None),
    keep_main_image: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update a property listing"""
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Update property attributes
    db_property.address = address
    db_property.property_type = property_type
    db_property.price_per_month = price_per_month
    db_property.square_footage = square_footage
    db_property.cat_friendly = cat_friendly
    db_property.air_conditioning = air_conditioning
    db_property.description = description
    db_property.contacts = contacts
    db_property.on_premises_parking = on_premises_parking
    
    # Handle main image updates
    if main_image and main_image.filename:
        # Remove existing main image
        existing_main = db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.is_main == True
        ).first()
        if existing_main:
            # Delete the old file
            old_file_path = f"app/static/images/{existing_main.filename}"
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            db.delete(existing_main)
        
        # Create property-specific images directory
        property_image_dir = f"app/static/images/property_{property_id}"
        os.makedirs(property_image_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = main_image.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{property_image_dir}/{unique_filename}"
        
        # Save the new file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(main_image.file, buffer)
        
        # Create new PropertyImage record
        db_image = PropertyImage(
            filename=unique_filename,
            is_main=True,
            property_id=property_id
        )
        db.add(db_image)
    elif keep_main_image != "true":
        # User wants to remove main image (no new image and not keeping existing)
        existing_main = db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.is_main == True
        ).first()
        if existing_main:
            # Delete the old file
            old_file_path = f"app/static/images/{existing_main.filename}"
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            db.delete(existing_main)
    
    db.commit()
    db.refresh(db_property)
    return db_property


@router.patch("/{property_id}")
def update_property_partial(
    property_id: int,
    travel_time_830am: Optional[float] = Body(None),
    travel_time_930am: Optional[float] = Body(None),
    travel_time_midday: Optional[float] = Body(None),
    travel_time_630pm: Optional[float] = Body(None),
    travel_time_730pm: Optional[float] = Body(None),
    contacts: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """Update property travel times"""
    # Get property
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Update travel times if provided
    if travel_time_830am is not None:
        db_property.travel_time_830am = travel_time_830am
    if travel_time_930am is not None:
        db_property.travel_time_930am = travel_time_930am
    if travel_time_midday is not None:
        db_property.travel_time_midday = travel_time_midday
    if travel_time_630pm is not None:
        db_property.travel_time_630pm = travel_time_630pm
    if travel_time_730pm is not None:
        db_property.travel_time_730pm = travel_time_730pm
    
    # Update contacts if provided
    if contacts is not None:
        db_property.contacts = contacts
    
    db.commit()
    db.refresh(db_property)
    return db_property


@router.post("/{property_id}/calculate-travel-times")
def calculate_travel_times(
    property_id: int, 
    use_tuesday: bool = False, 
    day_offset: int = 0, 
    db: Session = Depends(get_db)
):
    """
    Calculate travel times for a property.
    
    Args:
        property_id: Property ID
        use_tuesday: If True, use Tuesday instead of Monday (default: False)
        day_offset: Days to add/subtract from the target date (default: 0)
    """
    # Get property
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get global origin address from settings
    settings = db.query(Settings).first()
    if not settings or not settings.origin_address:
        raise HTTPException(status_code=400, detail="Global origin address not set")
    
    # Calculate travel times
    travel_time_service = TravelTimeService()
    try:
        travel_times = travel_time_service.calculate_travel_times(
            origin=settings.origin_address,
            destination=db_property.address,
            use_tuesday=use_tuesday,
            day_offset=day_offset
        )
        
        # Update property with travel times
        property_data = {
            "travel_time_830am": travel_times.get("travel_time_830am"),
            "travel_time_930am": travel_times.get("travel_time_930am"),
            "travel_time_midday": travel_times.get("travel_time_midday"),
            "travel_time_630pm": travel_times.get("travel_time_630pm"),
            "travel_time_730pm": travel_times.get("travel_time_730pm")
        }
        
        # Store metadata in property notes if anomalies detected
        anomalies = [key for key in travel_times.keys() if key.endswith('_anomaly') and travel_times[key]]
        if anomalies:
            note_content = f"Travel time anomalies detected on {travel_times.get('calculation_day', 'calculation day')}. "
            for key in anomalies:
                time_key = key.replace('_anomaly', '')
                note_content += f"{time_key}: {travel_times.get(f'{time_key}_note', 'Unusual traffic pattern')}. "
            
            # Add a note to the property
            note = PropertyNote(
                property_id=property_id,
                content=note_content,
                created_at=datetime.utcnow()
            )
            db.add(note)
            db.commit()
        
        # Update property with travel times
        for key, value in property_data.items():
            setattr(db_property, key, value)
        db.commit()
        db.refresh(db_property)
        
        # Create a response dictionary with property data
        response = db_property.__dict__.copy()
        
        # Remove SQLAlchemy state attributes
        if '_sa_instance_state' in response:
            del response['_sa_instance_state']
        
        # Add display formats to the response (won't be saved in DB)
        for key in ['travel_time_830am', 'travel_time_930am', 'travel_time_midday', 'travel_time_630pm', 'travel_time_730pm']:
            display_key = f"{key}_display"
            if display_key in travel_times:
                response[display_key] = travel_times[display_key]
        
        # Add calculation metadata
        response['calculation_day'] = travel_times.get('calculation_day', 'next Monday')
        response['calculation_timestamp'] = travel_times.get('calculation_timestamp')
        
        # Add anomaly flags if any
        for key in travel_times:
            if key.endswith('_anomaly') or key.endswith('_note'):
                response[key] = travel_times[key]
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{property_id}")
def delete_property(property_id: int, db: Session = Depends(get_db)):
    """Delete a property listing"""
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Delete associated images first
    image_dir = f"app/static/images/property_{property_id}"
    if os.path.exists(image_dir):
        shutil.rmtree(image_dir)
    
    db.delete(db_property)
    db.commit()
    return {"detail": "Property deleted"}
