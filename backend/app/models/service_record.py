"""ServiceRecord data model representing past maintenance and repair events."""

from typing import List
from pydantic import BaseModel, Field


class ServiceRecord(BaseModel):
    """Historical maintenance or repair record for a specific asset."""

    record_id: str = Field(..., description="Unique identifier for the service record")
    asset_id: str = Field(..., description="Target asset identifier")
    date: str = Field(..., description="Date of the service event in ISO or YYYY-MM-DD format")
    issue: str = Field(..., description="Reported problem or symptom")
    diagnosis: str = Field(..., description="Technician's findings and root cause analysis")
    action_taken: str = Field(..., description="Repair, calibration, or maintenance performed")
    parts_replaced: List[str] = Field(
        default_factory=list,
        description="List of component part numbers or names replaced during service",
    )
    technician_notes: str = Field(
        default="",
        description="Contextual commentary, observations, or warnings from the technician",
    )
