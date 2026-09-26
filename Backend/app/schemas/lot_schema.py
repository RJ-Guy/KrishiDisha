"""
Commodity Lot and Bulk Aggregation Pydantic Schemas for KrishiDisha.
Supports digital lot listings, quality parameters, moisture constraints,
and FPO bulk aggregation with full sub-lot origin traceability.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OwnerType(str, Enum):
    FARMER = "FARMER"
    FPO = "FPO"


class LotStatus(str, Enum):
    ACTIVE = "ACTIVE"
    AGGREGATED = "AGGREGATED"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    WITHDRAWN = "WITHDRAWN"


class QualityGrade(str, Enum):
    GRADE_A = "GRADE_A"
    GRADE_B = "GRADE_B"
    FAQ = "FAQ"  # Fair Average Quality


class StorageState(str, Enum):
    FARM_STORED = "FARM_STORED"
    WAREHOUSE = "WAREHOUSE"
    FRESHLY_HARVESTED = "FRESHLY_HARVESTED"


# ==========================================
# Quality Metrics Model
# ==========================================

class QualityMetrics(BaseModel):
    moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Moisture content percentage")
    foreign_matter_pct: Optional[float] = Field(default=0.0, ge=0.0, le=100.0, description="Foreign matter percentage")
    grain_size: Optional[str] = Field(default="MEDIUM", description="Grain size e.g. SMALL, MEDIUM, BOLD")
    damaged_grains_pct: Optional[float] = Field(default=0.0, ge=0.0, le=100.0, description="Damaged grains percentage")


# ==========================================
# Lot Base, Create, Update, Response
# ==========================================

class LotBase(BaseModel):
    commodity_id: int = Field(..., description="ID of the agricultural commodity (e.g., Wheat, Soybean)")
    commodity_name: Optional[str] = Field(default=None, description="Descriptive name of the commodity")
    variety: str = Field(..., min_length=1, max_length=100, description="Crop variety (e.g., Sharbati, Lokwan)")
    quantity_quintals: float = Field(..., gt=0.0, description="Quantity in Quintals (1 Quintal = 100 kg)")
    quality_grade: QualityGrade = Field(default=QualityGrade.FAQ, description="Quality grade classification")
    moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Moisture percentage (Premium grade requires <= 12%)")
    storage_state: StorageState = Field(default=StorageState.FARM_STORED, description="Holding/storage condition")
    location_address: Optional[str] = Field(default=None, description="Village/Mandi/Warehouse address")
    location_lat: float = Field(..., ge=-90.0, le=90.0, description="GPS Latitude")
    location_lng: float = Field(..., ge=-180.0, le=180.0, description="GPS Longitude")
    harvest_date: Optional[date] = Field(default=None, description="Date of crop harvest")
    expected_selling_window_start: Optional[date] = None
    expected_selling_window_end: Optional[date] = None
    minimum_acceptable_price: Optional[float] = Field(default=None, gt=0.0, description="Minimum reserve price per quintal in INR")

    @field_validator("moisture_pct")
    @classmethod
    def validate_moisture(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError("Moisture percentage must be between 0.0 and 100.0")
        return round(v, 2)


class LotCreate(LotBase):
    pass


class LotUpdate(BaseModel):
    variety: Optional[str] = Field(default=None, max_length=100)
    quantity_quintals: Optional[float] = Field(default=None, gt=0.0)
    quality_grade: Optional[QualityGrade] = None
    moisture_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    storage_state: Optional[StorageState] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    location_lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    expected_selling_window_start: Optional[date] = None
    expected_selling_window_end: Optional[date] = None
    minimum_acceptable_price: Optional[float] = Field(default=None, gt=0.0)
    status: Optional[LotStatus] = None


class LotResponse(LotBase):
    id: int
    owner_type: OwnerType
    owner_id: int
    owner_name: Optional[str] = None
    parent_bulk_lot_id: Optional[int] = None
    status: LotStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Bulk Aggregation & Traceability Schemas
# ==========================================

class SubLotContribution(BaseModel):
    child_lot_id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    quantity_quintals: float = Field(..., gt=0.0)
    moisture_pct: float
    quality_grade: QualityGrade
    contribution_share_pct: float = Field(..., ge=0.0, le=100.0, description="Proportion of total aggregated volume")

    model_config = ConfigDict(from_attributes=True)


class BulkLotCreate(BaseModel):
    commodity_id: int
    variety: str = Field(..., min_length=1, max_length=100)
    child_lot_ids: List[int] = Field(..., min_length=2, description="At least 2 child lots required to aggregate")
    aggregation_hub_lat: float = Field(..., ge=-90.0, le=90.0)
    aggregation_hub_lng: float = Field(..., ge=-180.0, le=180.0)
    hub_address: Optional[str] = Field(default=None, description="FPO aggregation center / collection point")
    minimum_acceptable_price: Optional[float] = Field(default=None, gt=0.0)


class AggregatedLotResponse(LotResponse):
    sub_lots: List[SubLotContribution] = Field(default_factory=list, description="Traceability list of all contributor farmers")
    total_contributing_farmers: int = 0
    weighted_average_moisture: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Query & Filter Parameters
# ==========================================

class LotFilterParams(BaseModel):
    commodity_id: Optional[int] = None
    commodity_name: Optional[str] = None
    min_quantity: Optional[float] = Field(default=None, ge=0.0)
    max_moisture: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    quality_grade: Optional[QualityGrade] = None
    owner_type: Optional[OwnerType] = None
    status: Optional[LotStatus] = LotStatus.ACTIVE
    max_distance_km: Optional[float] = Field(default=None, gt=0.0)
    user_lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    user_lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
