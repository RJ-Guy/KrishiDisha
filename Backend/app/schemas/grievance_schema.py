"""
Grievance Logging, Dispute Resolution, and Trust Auditing Pydantic Schemas
for KrishiDisha.
Supports transaction disputes (quality discrepancies, weight differences, payment delays)
and administrative resolution workflows.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class GrievanceCategory(str, Enum):
    QUALITY_DISPUTE = "QUALITY_DISPUTE"
    WEIGHT_DISCREPANCY = "WEIGHT_DISCREPANCY"
    PAYMENT_DELAY = "PAYMENT_DELAY"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    TRANSIT_DAMAGE = "TRANSIT_DAMAGE"
    OTHER = "OTHER"


class GrievanceStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


# ==========================================
# Grievance Schemas
# ==========================================

class GrievanceCreate(BaseModel):
    transaction_id: int = Field(..., description="Target transaction under dispute")
    category: GrievanceCategory
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed statement of dispute")
    evidence_urls: List[str] = Field(default_factory=list, description="Links to photographic proof, weighment slips, lab tests")
    claimed_amount: Optional[float] = Field(default=None, ge=0.0, description="Disputed compensation or refund amount in INR")


class GrievanceResolution(BaseModel):
    resolution_status: GrievanceStatus = Field(..., description="Must be RESOLVED or REJECTED")
    resolution_notes: str = Field(..., min_length=5, max_length=2000)
    refund_amount: Optional[float] = Field(default=0.0, ge=0.0, description="Refund approved to complainant")
    penalty_applied_to_user_id: Optional[int] = Field(default=None, description="User ID penalized (score deduction)")


class GrievanceResponse(BaseModel):
    id: int
    transaction_id: int
    raised_by_user_id: int
    raised_by_name: Optional[str] = None
    category: GrievanceCategory
    description: str
    evidence_urls: List[str] = Field(default_factory=list)
    claimed_amount: Optional[float] = None
    status: GrievanceStatus
    resolution_notes: Optional[str] = None
    refund_amount: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
