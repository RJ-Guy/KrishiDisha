"""
Machine Learning Price Forecast Pydantic Schemas for KrishiDisha.
Supports probabilistic price predictions, multi-day trajectories,
confidence intervals, and directional market trend indicators.
"""

from datetime import date
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ForecastTrend(str, Enum):
    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    STABLE = "STABLE"


# ==========================================
# Daily Trajectory Point
# ==========================================

class DailyForecastPoint(BaseModel):
    forecast_date: date
    predicted_modal_price: float = Field(..., description="Expected modal price in INR/Quintal")
    lower_bound: float = Field(..., description="Lower prediction interval (e.g. 10th percentile)")
    upper_bound: float = Field(..., description="Upper prediction interval (e.g. 90th percentile)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence estimate (0.0 to 1.0)")


# ==========================================
# Forecast Request & Response Schemas
# ==========================================

class ForecastRequest(BaseModel):
    commodity_id: int = Field(..., description="Commodity identifier")
    variety: Optional[str] = Field(default="Standard", description="Commodity variety")
    market_id: int = Field(..., description="Target APMC mandi identifier")
    horizon_days: int = Field(default=7, ge=1, le=30, description="Forecast horizon in days (e.g. 7, 14, 30)")
    current_market_price: Optional[float] = Field(default=None, description="Optional override for current modal price")


class ForecastResponse(BaseModel):
    commodity_id: int
    commodity_name: str
    market_id: int
    market_name: str
    forecast_date: date = Field(..., description="Inference anchor date")
    horizon_days: int = Field(..., description="Days ahead projected")
    current_modal_price: float = Field(..., description="Baseline modal price at time of inference")
    predicted_modal_price: float = Field(..., description="Projected modal price at horizon end")
    lower_bound: float = Field(..., description="Statistical lower bound at horizon end")
    upper_bound: float = Field(..., description="Statistical upper bound at horizon end")
    expected_price_change: float = Field(..., description="Predicted change in INR (Predicted - Current)")
    expected_price_change_pct: float = Field(..., description="Predicted percentage change")
    trend: ForecastTrend = Field(..., description="UPWARD, DOWNWARD, or STABLE")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence metric (e.g., 0.88)")
    trajectory: List[DailyForecastPoint] = Field(default_factory=list, description="Day-by-day projected price path")
    model_version: str = Field(default="v1.0-lightgbm", description="Artifact model version tag")
    recommendation_signal: str = Field(..., description="Plain language advisory e.g., 'Favorable to hold produce for 5-7 days'")

    model_config = ConfigDict(from_attributes=True)
