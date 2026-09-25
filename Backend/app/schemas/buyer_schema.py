"""
Buyer Requirements, Reverse Marketplace Tenders, and Multi-Factor
Matching Scoring Pydantic Schemas for KrishiDisha.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.lot_schema import QualityGrade


class BuyerCategory(str, Enum):
    INSTITUTIONAL = "INSTITUTIONAL"
    PROCESSOR = "PROCESSOR"
    EXPORTER = "EXPORTER"
    LOCAL_TRADER = "LOCAL_TRADER"


class RequirementStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# ==========================================
# Buyer Entity Schemas
# ==========================================

class BuyerResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    gst_no: Optional[str] = None
    trade_license: Optional[str] = None
    buyer_category: BuyerCategory = BuyerCategory.INSTITUTIONAL
    reliability_score: float = Field(default=100.0, ge=0.0, le=100.0, description="Trust metric (0-100)")
    verified: bool = False
    operating_states: List[str] = Field(default_factory=list)
    on_time_payment_rate_pct: float = Field(default=95.0, ge=0.0, le=100.0)
    total_deals_completed: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Buyer Requirements / Reverse Marketplace Tenders
# ==========================================

class BuyerRequirementBase(BaseModel):
    commodity_id: int = Field(..., description="ID of the required commodity")
    commodity_name: Optional[str] = None
    variety: str = Field(..., min_length=1, max_length=100)
    required_quantity_quintals: float = Field(..., gt=0.0, description="Total procurement volume in Quintals")
    max_price_per_quintal: float = Field(..., gt=0.0, description="Maximum purchase budget per quintal in INR")
    min_grade: QualityGrade = Field(default=QualityGrade.GRADE_A)
    max_moisture_pct: float = Field(default=12.0, ge=0.0, le=100.0, description="Hard constraint: Max moisture threshold")
    delivery_location_name: str = Field(..., min_length=2, max_length=200, description="Destination hub or warehouse name")
    delivery_location_lat: float = Field(..., ge=-90.0, le=90.0)
    delivery_location_lng: float = Field(..., ge=-180.0, le=180.0)
    delivery_window_start: date
    delivery_window_end: date
    special_conditions: Optional[str] = None


class BuyerRequirementCreate(BuyerRequirementBase):
    pass


class BuyerRequirementUpdate(BaseModel):
    required_quantity_quintals: Optional[float] = Field(default=None, gt=0.0)
    max_price_per_quintal: Optional[float] = Field(default=None, gt=0.0)
    min_grade: Optional[QualityGrade] = None
    max_moisture_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    delivery_location_name: Optional[str] = None
    delivery_location_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    delivery_location_lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    delivery_window_start: Optional[date] = None
    delivery_window_end: Optional[date] = None
    special_conditions: Optional[str] = None
    status: Optional[RequirementStatus] = None


class BuyerRequirementResponse(BuyerRequirementBase):
    id: int
    buyer_id: int
    company_name: str
    buyer_reliability_score: float
    status: RequirementStatus
    fulfilled_quantity_quintals: float = 0.0
    created_at: datetime
    expiry_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Multi-Factor Buyer Matching & Scoring
# ==========================================

class BuyerMatchScoreBreakdown(BaseModel):
    price_score: float = Field(..., ge=0.0, le=100.0, description="Weight w1 (Offer competitiveness)")
    distance_score: float = Field(..., ge=0.0, le=100.0, description="Weight w2 (Proximity / freight burden)")
    quality_fit_score: float = Field(..., ge=0.0, le=100.0, description="Weight w3 (Grade & moisture match)")
    reliability_score: float = Field(..., ge=0.0, le=100.0, description="Weight w4 (Buyer settlement history)")
    volume_compatibility_score: float = Field(..., ge=0.0, le=100.0, description="Weight w5 (Batch lot fulfillment fit)")


class BuyerMatchResult(BaseModel):
    buyer_id: int
    company_name: str
    requirement_id: Optional[int] = None
    offered_price_per_quintal: float
    distance_km: float
    overall_match_score: float = Field(..., ge=0.0, le=100.0, description="Overall weighted score (0-100)")
    score_breakdown: BuyerMatchScoreBreakdown
    human_readable_explanation: str = Field(..., description="E.g. '94% Match: High price offer ₹2,620, only 18 km away, 98% on-time payment track record'")
    estimated_transport_cost: float
    estimated_net_realization: float = Field(..., description="Projected net earnings after freight & handling")
    is_hard_filter_passed: bool = True
    disqualification_reason: Optional[str] = None


class BuyerMatchQuery(BaseModel):
    lot_id: Optional[int] = None
    commodity_id: int
    variety: Optional[str] = None
    quantity_quintals: float = Field(..., gt=0.0)
    moisture_pct: float = Field(..., ge=0.0, le=100.0)
    quality_grade: QualityGrade
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lng: float = Field(..., ge=-180.0, le=180.0)
    max_distance_km: Optional[float] = Field(default=250.0, gt=0.0)
