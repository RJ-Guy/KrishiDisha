"""
Net Realization Engine, Decision Analytics (SELL/WAIT/BEST BUYER),
and Variance Audit Report Pydantic Schemas for KrishiDisha.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DecisionVerdict(str, Enum):
    SELL_NOW = "SELL_NOW"
    WAIT = "WAIT"
    BEST_BUYER = "BEST_BUYER"


class SellingChannel(str, Enum):
    MANDI = "MANDI"
    INSTITUTIONAL_BUYER = "INSTITUTIONAL_BUYER"
    MSP_CENTER = "MSP_CENTER"
    FPO_POOL = "FPO_POOL"


class LiquidityUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ==========================================
# Net Realization Breakdown
# ==========================================

class NetRealizationItem(BaseModel):
    channel: SellingChannel
    destination_name: str = Field(..., description="Name of APMC Mandi, Buyer entity, or MSP Center")
    headline_price_per_quintal: float = Field(..., description="Gross quoted price")
    gross_revenue: float = Field(..., description="Quantity * Headline Price")
    transport_cost: float = Field(..., ge=0.0, description="Estimated freight deduction")
    storage_cost: float = Field(default=0.0, ge=0.0, description="Storage holding fee")
    handling_cost: float = Field(default=0.0, ge=0.0, description="Loading/unloading/bagging")
    mandi_cess_and_taxes: float = Field(default=0.0, ge=0.0, description="Statutory market cess")
    net_realization: float = Field(..., description="Gross - Transport - Storage - Handling - Cess")
    net_price_per_quintal: float = Field(..., description="Net Realization / Quantity")
    distance_km: float = Field(..., ge=0.0)
    explanation: Optional[str] = None


class MSPComparisonItem(BaseModel):
    msp_price_per_quintal: float
    agency_name: str
    center_location: str
    distance_km: float
    net_realization_msp: float
    is_above_msp: bool = Field(..., description="True if best market option exceeds government MSP")
    premium_over_msp_per_quintal: float = Field(..., description="Best market net price minus MSP")


# ==========================================
# Decision Engine Request & Recommendation
# ==========================================

class DecisionRequest(BaseModel):
    lot_id: Optional[int] = None
    commodity_id: int
    variety: Optional[str] = "Standard"
    quantity_quintals: float = Field(..., gt=0.0, description="Volume to sell")
    quality_grade: str = Field(default="GRADE_A", description="GRADE_A, GRADE_B, FAQ")
    moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Moisture reading")
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lng: float = Field(..., ge=-180.0, le=180.0)
    origin_address: Optional[str] = None
    storage_available: bool = Field(default=True, description="Whether farmer has safe storage access")
    storage_cost_per_quintal_day: float = Field(default=0.50, ge=0.0, description="Daily holding tariff per quintal in INR")
    liquidity_urgency: LiquidityUrgency = Field(default=LiquidityUrgency.MEDIUM, description="Need for immediate cash")
    holding_horizon_days: int = Field(default=7, ge=1, le=30, description="Target evaluation window for holding")


class DecisionRecommendationResponse(BaseModel):
    verdict: DecisionVerdict = Field(..., description="SELL NOW, WAIT, or BEST BUYER")
    headline_summary: str = Field(..., description="Executive takeaway e.g. 'SELL NOW: Local Mandi yields highest net realization'")
    plain_text_explanation: str = Field(..., description="Non-technical justification for farmer/FPO")
    best_channel: SellingChannel
    best_destination_name: str
    expected_net_realization: float
    expected_net_price_per_quintal: float
    channel_comparisons: List[NetRealizationItem] = Field(default_factory=list, description="Ranked options by net outcome")
    forecast_price_delta: float = Field(..., description="Projected price change over holding horizon")
    estimated_holding_cost: float = Field(..., description="Storage cost + risk penalty over horizon")
    msp_benchmark: Optional[MSPComparisonItem] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Variance & Post-Fulfillment Audit Report
# ==========================================

class VarianceItem(BaseModel):
    category: str = Field(..., description="E.g., Gross Revenue, Freight, Storage, Handling, Quality Deduction")
    expected_amount: float
    actual_amount: float
    variance_amount: float = Field(..., description="Actual - Expected (positive is favorable)")
    variance_pct: float


class RealizationVarianceReport(BaseModel):
    transaction_id: int
    seller_name: str
    commodity_name: str
    quantity_quintals: float
    expected_net_realization: float
    actual_net_realization: float
    total_variance_amount: float = Field(..., description="Actual Net Realization - Expected Net Realization")
    total_variance_pct: float
    itemized_variances: List[VarianceItem] = Field(default_factory=list)
    feedback_insights: str = Field(..., description="Algorithmic lesson logged to improve future estimates")
    settled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
