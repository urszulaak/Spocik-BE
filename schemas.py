from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date as DateType
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
    date: DateType
    description: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    date: Optional[DateType] = None
    description: Optional[str] = None

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