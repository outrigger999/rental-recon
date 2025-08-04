from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class PropertyImageBase(BaseModel):
    is_main: bool = False


class PropertyImageCreate(PropertyImageBase):
    pass


class PropertyImage(PropertyImageBase):
    id: int
    filename: str
    property_id: int

    class Config:
        orm_mode = True


class PropertyNoteBase(BaseModel):
    content: str


class PropertyNoteCreate(PropertyNoteBase):
    pass


class PropertyNote(PropertyNoteBase):
    id: int
    created_at: datetime
    property_id: int

    class Config:
        orm_mode = True


class PropertyBase(BaseModel):
    address: str
    property_type: str
    price_per_month: float
    square_footage: float
    description: Optional[str] = None
    contacts: Optional[str] = None
    cat_friendly: bool = False
    air_conditioning: bool = False
    on_premises_parking: bool = False
    travel_time_830am: Optional[float] = None
    travel_time_930am: Optional[float] = None
    travel_time_midday: Optional[float] = None
    travel_time_630pm: Optional[float] = None
    travel_time_730pm: Optional[float] = None


class PropertyCreate(PropertyBase):
    pass


class Property(PropertyBase):
    id: int
    images: List[PropertyImage] = []
    notes: List[PropertyNote] = []

    class Config:
        orm_mode = True
