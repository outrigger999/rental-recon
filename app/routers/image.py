import os
import uuid
import base64
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.property import Property, PropertyImage

router = APIRouter()

def ensure_image_dir(property_id: int):
    """Ensure the image directory exists for a property"""
    image_dir = f"app/static/images/property_{property_id}"
    os.makedirs(image_dir, exist_ok=True)
    return image_dir


@router.post("/{property_id}/upload")
async def upload_image(
    property_id: int,
    is_main: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image file for a property"""
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Create directory for property images if it doesn't exist
    image_dir = ensure_image_dir(property_id)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(image_dir, unique_filename)
    
    # Save the file
    with open(file_path, "wb") as image_file:
        image_file.write(await file.read())
    
    # If this is the main image and there's an existing main image, update it
    if is_main:
        existing_main = db.query(PropertyImage).filter(
            PropertyImage.property_id == property_id,
            PropertyImage.is_main == True
        ).first()
        if existing_main:
            existing_main.is_main = False
    
    # Create image record in database
    db_image = PropertyImage(
        filename=unique_filename,
        is_main=is_main,
        property_id=property_id
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return {
        "id": db_image.id,
        "filename": db_image.filename,
        "is_main": db_image.is_main
    }


@router.post("/{property_id}/paste")
async def paste_image(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Save a pasted base64 image for a property"""
    # Parse request body for base64 image data
    data = await request.json()
    if "image_data" not in data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Process the base64 image data
    try:
        image_data = data["image_data"]
        # Remove data URL prefix if present
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Decode base64 data
        image_bytes = base64.b64decode(image_data)
        
        # Create directory for property images if it doesn't exist
        image_dir = ensure_image_dir(property_id)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.png"  # Assuming PNG for pasted images
        file_path = os.path.join(image_dir, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)
        
        # If this is the main image and there's an existing main image, update it
        is_main = data.get("is_main", True)  # Default to main image for pasted images
        if is_main:
            existing_main = db.query(PropertyImage).filter(
                PropertyImage.property_id == property_id,
                PropertyImage.is_main == True
            ).first()
            if existing_main:
                existing_main.is_main = False
                db.commit()
        
        # Create image record in database
        db_image = PropertyImage(
            filename=unique_filename,
            is_main=is_main,
            property_id=property_id
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return {
            "id": db_image.id,
            "filename": db_image.filename,
            "is_main": db_image.is_main
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


@router.delete("/{property_id}/images/{image_id}")
def delete_image(
    property_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """Delete an image for a property"""
    # Check if image exists and belongs to the property
    db_image = db.query(PropertyImage).filter(
        PropertyImage.id == image_id,
        PropertyImage.property_id == property_id
    ).first()
    
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete the image file
    image_path = f"app/static/images/property_{property_id}/{db_image.filename}"
    if os.path.exists(image_path):
        os.remove(image_path)
    
    # Delete image record from database
    db.delete(db_image)
    db.commit()
    
    return {"detail": "Image deleted"}
