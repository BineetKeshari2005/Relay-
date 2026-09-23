"""Technician session and conversation turn models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    """Single turn within a technician-Relay dialogue."""

    turn_id: str = Field(..., description="Unique turn identifier")
    session_id: str = Field(..., description="Parent session ID")
    speaker: Literal["technician", "assistant", "system"] = Field(
        ...,
        description="Originator of this message",
    )
    text: str = Field(..., description="Utterance text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of utterance",
    )


class TechnicianSession(BaseModel):
    """Active diagnostic session between a technician and Relay."""

    session_id: str = Field(..., description="Unique session identifier")
    technician_id: str = Field(..., description="Technician identifier or badge number")
    asset_id: str = Field(..., description="Target equipment identifier under inspection")
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Session start timestamp",
    )
    current_issue: Optional[str] = Field(
        None,
        description="Technician-reported symptom or situation",
    )
    current_error_code: Optional[str] = Field(
        None,
        description="Diagnostic trouble code (e.g. E17)",
    )
    current_measurements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Live physical measurements (e.g. {'pressure_psi': 195, 'ambient_temp_f': 82})",
    )
    status: Literal["active", "resolved", "escalated", "aborted"] = Field(
        default="active",
        description="Session state",
    )
