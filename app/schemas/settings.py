from pydantic import BaseModel


class SettingsBase(BaseModel):
    origin_address: str = ""


class SettingsCreate(SettingsBase):
    pass


class SettingsUpdate(SettingsBase):
    pass


class Settings(SettingsBase):
    id: int

    class Config:
        orm_mode = True
