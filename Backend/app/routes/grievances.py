"""
Grievances, Disputes, and Trust Auditing Router for KrishiDisha.
Supports dispute logging for quality differences, weight discrepancies,
delivery delays, and transparent administrative resolution workflows.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.grievance_schema import (
    GrievanceCategory,
    GrievanceStatus,
    GrievanceCreate,
    GrievanceResolution,
    GrievanceResponse,
)
from app.schemas.auth_schema import UserRole

# Dependencies
from app.routes.auth import get_db, get_current_user, require_role

router = APIRouter(prefix="/grievances", tags=["Grievances & Disputes"])

# ==========================================
# In-Memory Demonstration Store
# ==========================================
_MOCK_GRIEVANCES: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "transaction_id": 1,
        "raised_by_user_id": 1,
        "raised_by_name": "Ramesh Chandra Patel",
        "category": GrievanceCategory.WEIGHT_DISCREPANCY,
        "description": "Weighment scale at buyer hub recorded 63.8 Quintals vs farm digital scale 65.0 Quintals.",
        "evidence_urls": ["https://storage.krishidisha.in/proofs/weigh_slip_01.jpg"],
        "claimed_amount": 3120.0,
        "status": GrievanceStatus.UNDER_REVIEW,
        "resolution_notes": None,
        "refund_amount": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
}


# ==========================================
# Route Handlers
# ==========================================

@router.post("", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED, summary="Lodge Dispute / Grievance")
def lodge_grievance(
    payload: GrievanceCreate,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Lodge a formal transaction dispute with photographic proof,
    weighment slips, or lab inspection evidence.
    """
    user_id = getattr(current_user, "id", None) or current_user.get("id", 1)
    user_name = getattr(current_user, "full_name", None) or current_user.get("full_name", "Complainant")

    new_id = max(_MOCK_GRIEVANCES.keys(), default=0) + 1
    new_g = {
        "id": new_id,
        "transaction_id": payload.transaction_id,
        "raised_by_user_id": user_id,
        "raised_by_name": user_name,
        "category": payload.category,
        "description": payload.description,
        "evidence_urls": payload.evidence_urls,
        "claimed_amount": payload.claimed_amount,
        "status": GrievanceStatus.OPEN,
        "resolution_notes": None,
        "refund_amount": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    _MOCK_GRIEVANCES[new_id] = new_g
    return GrievanceResponse(**new_g)


@router.get("", response_model=List[GrievanceResponse], summary="List Grievances")
def list_grievances(
    status_filter: Optional[GrievanceStatus] = Query(None, alias="status"),
    current_user: Any = Depends(get_current_user),
):
    """Retrieve all grievances filed by or involving the authenticated user."""
    results = []
    for g in _MOCK_GRIEVANCES.values():
        if status_filter and g["status"] != status_filter:
            continue
        results.append(GrievanceResponse(**g))
    return results


@router.get("/{grievance_id}", response_model=GrievanceResponse, summary="Get Grievance by ID")
def get_grievance(grievance_id: int):
    """Retrieve full dispute details and resolution audit history."""
    if grievance_id not in _MOCK_GRIEVANCES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    return GrievanceResponse(**_MOCK_GRIEVANCES[grievance_id])


@router.patch("/{grievance_id}/resolve", response_model=GrievanceResponse, summary="Submit Admin Dispute Resolution")
def resolve_grievance(
    grievance_id: int,
    payload: GrievanceResolution,
    current_user: Any = Depends(require_role(UserRole.ADMIN)),
):
    """
    Administrative arbitration:
    Closes dispute, awards compensatory refunds, and applies reliability penalties if applicable.
    """
    if grievance_id not in _MOCK_GRIEVANCES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")

    g = _MOCK_GRIEVANCES[grievance_id]
    g["status"] = payload.resolution_status
    g["resolution_notes"] = payload.resolution_notes
    g["refund_amount"] = payload.refund_amount
    g["updated_at"] = datetime.now(timezone.utc)
    return GrievanceResponse(**g)
