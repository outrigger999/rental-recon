from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.property import Property, PropertyNote
from ..schemas.property import PropertyNote as PropertyNoteSchema, PropertyNoteCreate

router = APIRouter()

@router.post("/{property_id}/notes", response_model=PropertyNoteSchema)
def add_note(
    property_id: int,
    note: PropertyNoteCreate,
    db: Session = Depends(get_db)
):
    """Add a note to a property"""
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Create note
    db_note = PropertyNote(**note.dict(), property_id=property_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.get("/{property_id}/notes", response_model=List[PropertyNoteSchema])
def get_property_notes(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get all notes for a property"""
    # Check if property exists
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return db_property.notes

@router.delete("/{property_id}/notes/{note_id}")
def delete_note(
    property_id: int,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a note from a property"""
    # Check if note exists and belongs to the property
    db_note = db.query(PropertyNote).filter(
        PropertyNote.id == note_id,
        PropertyNote.property_id == property_id
    ).first()
    
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(db_note)
    db.commit()
    
    return {"detail": "Note deleted"}
