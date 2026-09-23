"""Demo data inspection endpoints for validating assets and technician sessions."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.data.demo_fixtures import (
    get_demo_asset,
    get_demo_session,
    get_demo_service_records,
    get_demo_turns,
)
from app.models.asset import Asset
from app.models.session import TechnicianSession, ConversationTurn
from app.models.service_record import ServiceRecord
from typing import List

router = APIRouter(prefix="/api/demo", tags=["Demo Data"])


class SessionDetailResponse(BaseModel):
    """Detailed view of a technician session including history and active turns."""

    session: TechnicianSession
    asset: Asset
    service_history: List[ServiceRecord] = Field(default_factory=list)
    recent_turns: List[ConversationTurn] = Field(default_factory=list)


@router.get(
    "/asset/{asset_id}",
    response_model=Asset,
    summary="Get Demo Equipment Asset",
    responses={
        404: {"description": "Asset not found in demo fixture set"},
    },
)
async def get_asset_endpoint(asset_id: str) -> Asset:
    """Retrieve equipment specifications and metadata for a demo asset (e.g., ACX-420-017)."""
    asset = get_demo_asset(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "AssetNotFound",
                "message": f"Asset with ID '{asset_id}' not found in demo database.",
                "available_assets": ["ACX-420-017"],
            },
        )
    return asset


@router.get(
    "/session/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get Demo Technician Session",
    responses={
        404: {"description": "Session not found in demo fixture set"},
    },
)
async def get_session_endpoint(session_id: str) -> SessionDetailResponse:
    """Retrieve full session state including active measurements, dialogue turns, and asset details."""
    session = get_demo_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SessionNotFound",
                "message": f"Session with ID '{session_id}' not found.",
                "available_sessions": ["sess-017"],
            },
        )

    asset = get_demo_asset(session.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "AssetNotFoundForSession",
                "message": f"Asset '{session.asset_id}' associated with session '{session_id}' was not found.",
            },
        )

    history = get_demo_service_records(session.asset_id)
    turns = get_demo_turns(session_id)

    return SessionDetailResponse(
        session=session,
        asset=asset,
        service_history=history,
        recent_turns=turns,
    )
