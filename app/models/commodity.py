"""Commodity data models."""
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from datetime import datetime


class CommodityBase(BaseModel):
    """Base commodity model."""
    name: str = Field(..., description="Commodity name (e.g., 'cashew', 'rubber')")
    category: str = Field(..., description="Commodity category (e.g., 'nut', 'latex')")
    metadata: Optional[Dict[str, Any]] = None


class CommodityCreate(CommodityBase):
    """Commodity creation model."""
    pass


class Commodity(CommodityBase):
    """Full commodity model with ID."""
    id: UUID = Field(default_factory=uuid4)

    class Config:
        from_attributes = True


class CommodityInDB(Commodity):
    """Commodity model as stored in database."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
