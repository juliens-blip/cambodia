"""Price data models."""
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal


class PriceBase(BaseModel):
    """Base price model."""
    commodity_id: UUID
    date: date
    price_usd_per_unit: Decimal = Field(..., ge=0, decimal_places=2)
    volume_tons: Optional[int] = Field(None, ge=0)
    source: str = Field(..., description="Data source: 'MEF', 'WITS', 'ODC', 'manual'")
    destination_country: Optional[str] = None
    quality_grade: Optional[str] = Field(None, description="e.g., 'W320', 'W240' for cashew")
    metadata: Optional[Dict[str, Any]] = None


class PriceCreate(PriceBase):
    """Price creation model."""
    pass


class Price(PriceBase):
    """Full price model with ID."""
    id: UUID = Field(default_factory=uuid4)

    class Config:
        from_attributes = True


class PriceInDB(Price):
    """Price model as stored in database."""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceWithContext(Price):
    """Price with market context for ChromaDB storage."""
    market_conditions: Optional[list[str]] = Field(
        None,
        description="Market conditions: ['high_demand', 'supply_shortage', 'price_spike', etc.]"
    )
    context_description: Optional[str] = Field(
        None,
        description="Natural language context for semantic search"
    )
