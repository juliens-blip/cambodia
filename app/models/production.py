"""Production data models."""
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class GeoLocation(BaseModel):
    """Geographic location coordinates."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class ProductionBase(BaseModel):
    """Base production model."""
    commodity_id: UUID
    year: int = Field(..., ge=1900, le=2100)
    province: str
    area_hectares: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    production_tons: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    yield_kg_per_ha: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    geolocation: Optional[GeoLocation] = None
    source: str = Field(..., description="Data source: 'MEF', 'WITS', 'ODC', 'GDrive'")


class ProductionCreate(ProductionBase):
    """Production creation model."""
    pass


class Production(ProductionBase):
    """Full production model with ID."""
    id: UUID = Field(default_factory=uuid4)

    class Config:
        from_attributes = True


class ProductionInDB(Production):
    """Production model as stored in database."""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductionWithContext(Production):
    """Production with context for ChromaDB storage."""
    context_description: Optional[str] = Field(
        None,
        description="Natural language description for semantic search"
    )

    def generate_context(self) -> str:
        """Generate context description from production data."""
        parts = [f"{self.province}:"]

        if self.area_hectares:
            parts.append(f"{self.area_hectares} hectares")

        if self.production_tons:
            parts.append(f"{self.production_tons} tons production")

        if self.yield_kg_per_ha:
            parts.append(f"yield {self.yield_kg_per_ha}kg/ha")

        return " ".join(parts)
