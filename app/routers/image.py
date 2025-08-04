import os
import uuid
import base64
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from pathlib import Path
from ..database import get_db
from ..models.property import Property, PropertyImage
from ..services.image_processor import ImageProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def ensure_image_dir(property_id: int) -> str:
    """
    Ensure the image directory exists for a property.
    
    Args:
        property_id: ID of the property
        
    Returns:
        Path to the image directory
    """
    image_dir = os.path.abspath(f"app/static/images/property_{property_id}")
    os.makedirs(image_dir, exist_ok=True)
    return image_dir


async def process_and_save_image(
    file: UploadFile,
    property_id: int,
    is_main: bool,
    db: Session
) -> PropertyImage:
    """
    Process, optimize, and save an uploaded image.
    
    Args:
        file: Uploaded file object
        property_id: ID of the property this image belongs to
        is_main: Whether this is the main image for the property
        db: Database session
        
    Returns:
        The created PropertyImage record
    """
    # Ensure the image directory exists
    image_dir = ensure_image_dir(property_id)
    
    try:
        # Process and optimize the image
        processed_image, new_filename = await _process_uploaded_image(file, image_dir)
        
        # If this is the main image and there's an existing main image, update it
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
            filename=new_filename,
            is_main=is_main,
            property_id=property_id
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return db_image
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        # Clean up any partially saved files
        if 'new_filename' in locals():
            temp_path = os.path.join(image_dir, new_filename)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        raise


async def _process_uploaded_image(
    file: UploadFile,
    output_dir: str
) -> Tuple[bytes, str]:
    """
    Process an uploaded image file.
    
    Args:
        file: Uploaded file object
        output_dir: Directory to save the processed image
        
    Returns:
        Tuple of (processed_image_data, new_filename)
    """
    try:
        # Process the image using our ImageProcessor
        image_processor = ImageProcessor()
        
        # Get the file extension from the original filename
        file_extension = Path(file.filename).suffix.lower()
        
        # Process the image
        processed_image, new_filename = await image_processor.process_uploaded_file(
            file=file,
            target_format='JPEG'  # Convert all images to JPEG for consistency
        )
        
        # Save the processed image
        output_path = os.path.join(output_dir, new_filename)
        with open(output_path, 'wb') as f:
            f.write(processed_image)
            
        return processed_image, new_filename
        
    except Exception as e:
        logger.error(f"Error in _process_uploaded_image: {str(e)}", exc_info=True)
        raise


@router.post("/{property_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    property_id: int,
    is_main: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and optimize an image file for a property.
    
    Supports various image formats including HEIC/HEIF (automatically converted to JPEG).
    Images are automatically optimized for web use.
    """
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    try:
        # Process and save the uploaded image
        db_image = await process_and_save_image(
            file=file,
            property_id=property_id,
            is_main=is_main,
            db=db
        )
        
        return {
            "id": db_image.id,
            "filename": db_image.filename,
            "is_main": db_image.is_main,
            "message": "Image uploaded and optimized successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/{property_id}/paste", status_code=status.HTTP_201_CREATED)
async def paste_image(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Save a pasted base64 image for a property.
    
    The image will be automatically optimized for web use.
    """
    # Parse request body for base64 image data
    data = await request.json()
    if "image_data" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image data provided"
        )
    
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    try:
        # Process the base64 image data
        image_data = data["image_data"]
        is_main = data.get("is_main", True)  # Default to main image for pasted images
        
        # Create a mock UploadFile for the pasted image
        from fastapi.datastructures import UploadFile
        from io import BytesIO
        
        # Process the image
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        # Decode base64 data
        image_bytes = base64.b64decode(image_data)
        
        # Create a file-like object for the image processor
        file_obj = BytesIO(image_bytes)
        file_obj.filename = f"pasted_image.png"
        
        # Create a mock UploadFile
        file = UploadFile(
            filename=file_obj.filename,
            file=file_obj,
            content_type="image/png"
        )
        
        # Process and save the image
        db_image = await process_and_save_image(
            file=file,
            property_id=property_id,
            is_main=is_main,
            db=db
        )
        
        return {
            "id": db_image.id,
            "filename": db_image.filename,
            "is_main": db_image.is_main,
            "message": "Pasted image processed and saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing pasted image: {str(e)}"
        )


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
