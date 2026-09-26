"""
Market Intelligence, Mandi Prices, Historical Trends, and MSP Benchmarks
Pydantic Schemas for KrishiDisha.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class PriceTrend(str, Enum):
    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    STABLE = "STABLE"


# ==========================================
# Market / Mandi Schemas
# ==========================================

class MandiBase(BaseModel):
    market_name: str = Field(..., min_length=2, max_length=150, description="Name of the APMC Mandi / Market")
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_apmc: bool = Field(default=True, description="Whether this is a regulated APMC market")
    operating_days: Optional[str] = Field(default="Mon-Sat", description="Weekly operating days")


class MandiCreate(MandiBase):
    pass


class MandiResponse(MandiBase):
    id: int
    distance_km: Optional[float] = Field(default=None, description="Calculated road distance from user origin")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Market Price Schemas
# ==========================================

class MarketPriceCreate(BaseModel):
    market_id: int
    commodity_id: int
    variety: str = Field(..., min_length=1, max_length=100)
    arrival_date: date
    min_price: float = Field(..., ge=0.0, description="Minimum price per quintal in INR")
    max_price: float = Field(..., ge=0.0, description="Maximum price per quintal in INR")
    modal_price: float = Field(..., ge=0.0, description="Modal (most frequent) price per quintal in INR")
    arrivals_volume_tonnes: float = Field(default=0.0, ge=0.0, description="Daily arrival quantity in tonnes")


class MarketPriceResponse(BaseModel):
    id: int
    market_id: int
    market_name: str
    state: str
    district: str
    commodity_id: int
    commodity_name: str
    variety: str
    arrival_date: date
    min_price: float
    max_price: float
    modal_price: float
    arrivals_volume_tonnes: float
    distance_km: Optional[float] = None
    estimated_net_realization_per_quintal: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MandiPriceFilter(BaseModel):
    commodity_id: Optional[int] = None
    commodity_name: Optional[str] = None
    variety: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    market_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    user_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    user_lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    max_distance_km: Optional[float] = Field(default=None, gt=0.0)


# ==========================================
# Price Trends & Historical Analytics
# ==========================================

class PriceTrendPoint(BaseModel):
    date: date
    modal_price: float
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    arrivals_volume_tonnes: float = 0.0


class HistoricalPriceQuery(BaseModel):
    commodity_id: int
    market_id: int
    days_lookback: int = Field(default=30, ge=7, le=365)


class MarketTrendsResponse(BaseModel):
    commodity_id: int
    commodity_name: str
    market_id: int
    market_name: str
    series: List[PriceTrendPoint]
    average_price_7d: float
    average_price_30d: float
    trend: PriceTrend
    price_change_pct: float = Field(..., description="Percentage change in modal price over the window")
    volatility_score: Optional[float] = Field(default=None, description="Price dispersion metric")


# ==========================================
# MSP & Government Procurement
# ==========================================

class ProcurementOptionCreate(BaseModel):
    commodity_id: int
    msp_price: float = Field(..., gt=0.0, description="Minimum Support Price per quintal in INR")
    agency_name: str = Field(..., min_length=2, max_length=150, description="E.g., FCI, NAFED, HAFED")
    center_location: str = Field(..., min_length=2, max_length=200)
    state: str
    district: str
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    active: bool = True


class ProcurementOptionResponse(BaseModel):
    id: int
    commodity_id: int
    commodity_name: str
    msp_price: float
    agency_name: str
    center_location: str
    state: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    active: bool
    distance_km: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
