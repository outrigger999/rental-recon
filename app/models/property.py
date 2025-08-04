from datetime import datetime
from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from ..database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    property_type = Column(String)  # Home, Townhome, Apartment
    price_per_month = Column(Float)
    square_footage = Column(Float)
    description = Column(Text, nullable=True)
    contacts = Column(Text, nullable=True)
    cat_friendly = Column(Boolean, default=False)
    air_conditioning = Column(Boolean, default=False)
    on_premises_parking = Column(Boolean, default=False)
    
    # Travel time fields (minutes)
    travel_time_830am = Column(Float, nullable=True)
    travel_time_930am = Column(Float, nullable=True)
    travel_time_midday = Column(Float, nullable=True)
    travel_time_630pm = Column(Float, nullable=True)
    travel_time_730pm = Column(Float, nullable=True)
    
    # Relationships
    images = relationship("PropertyImage", back_populates="property")
    notes = relationship("PropertyNote", back_populates="property", cascade="all, delete-orphan")


class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    is_main = Column(Boolean, default=False)
    property_id = Column(Integer, ForeignKey("properties.id"))
    
    # Image metadata
    width = Column(Integer, nullable=True)  # Image width in pixels
    height = Column(Integer, nullable=True)  # Image height in pixels
    format = Column(String(10), nullable=True)  # Image format (e.g., 'JPEG', 'PNG')
    size_kb = Column(Float, nullable=True)  # File size in kilobytes
    is_optimized = Column(Boolean, default=False)  # Whether the image has been optimized
    original_format = Column(String(10), nullable=True)  # Original format if converted
    
    # Relationship with property
    property = relationship("Property", back_populates="images")


class PropertyNote(Base):
    __tablename__ = "property_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    property_id = Column(Integer, ForeignKey("properties.id"))
    
    # Relationship with property
    property = relationship("Property", back_populates="notes")
