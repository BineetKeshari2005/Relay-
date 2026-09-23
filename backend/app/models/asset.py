"""Asset data model representing physical equipment under service."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Asset(BaseModel):
    """Represents a physical equipment asset (e.g., HVAC rooftop unit)."""

    asset_id: str = Field(..., description="Unique identifier for the asset (e.g., ACX-420-017)")
    model: str = Field(..., description="Equipment model name/number (e.g., ACX-420)")
    manufacturer: str = Field(..., description="Equipment manufacturer (e.g., CoolCore)")
    location: str = Field(..., description="Physical installation location (e.g., Facility 4, Rooftop B)")
    status: str = Field(
        default="operational",
        description="Current operational status (e.g., operational, maintenance_required, offline)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom technical metadata (serial number, install date, specs, refrigerant type, etc.)",
    )
