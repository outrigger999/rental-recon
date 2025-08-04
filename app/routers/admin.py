from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db, Base, engine
from ..models.property import Property, PropertyImage, PropertyNote
from ..models.settings import Settings

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.post("/reset-database")
def reset_database(db: Session = Depends(get_db)):
    """Clear all data from the database (testing purposes only)"""
    # Delete all records from all tables
    db.query(PropertyNote).delete()
    db.query(PropertyImage).delete()
    db.query(Property).delete()
    db.query(Settings).delete()
    db.commit()
    
    # Recreate all tables (will keep the structure but remove all data)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    return {"message": "Database has been reset successfully"}
