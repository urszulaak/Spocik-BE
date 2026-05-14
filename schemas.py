from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID
from datetime import date
from typing import Optional, Dict

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    is_admin: bool
    
    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    name: str
    type: str
    date: date
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

class Link(BaseModel):
    href: str
    method: str

class EventResponse(EventBase):
    id: UUID
    week: int
    month: int
    year: int
    author: UserResponse
    links: Optional[Dict[str, Link]] = Field(default=None, alias="_links")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)