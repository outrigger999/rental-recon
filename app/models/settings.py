from sqlalchemy import Column, Integer, String
from ..database import Base

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    origin_address = Column(String, default="")
