"""
CSX Index Model
Stores Cambodia Stock Exchange index values for persistence and fallback
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CSXIndexCreate(BaseModel):
    """Schema for creating a new CSX index entry"""
    value: float = Field(..., description="CSX index value", ge=0)
    change_percent: Optional[float] = Field(None, description="Percentage change from previous day")


class CSXIndexResponse(BaseModel):
    """Schema for CSX index response"""
    id: int
    value: float
    change_percent: Optional[float] = None
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CSXIndexLatest(BaseModel):
    """Schema for latest CSX index (simplified for UI)"""
    value: float
    change_percent: Optional[float] = None
    updated_at: str  # ISO format string for easy serialization
