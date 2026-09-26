"""
Logistics, Fleet Routing, Tariff Calculation, and Vehicle Dispatch
Pydantic Schemas for KrishiDisha.
Supports vehicle classification (1.5T Mini, 5T Medium, 16T Heavy),
distance matrices, freight quotes, and consolidated pooling savings.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class VehicleType(str, Enum):
    MINI_TRUCK_1_5T = "MINI_TRUCK_1_5T"     # E.g., Tata Ace / Bolero (15 Quintals)
    MEDIUM_TRUCK_5T = "MEDIUM_TRUCK_5T"     # E.g., Eicher / 14-ft (50 Quintals)
    HEAVY_TRUCK_16T = "HEAVY_TRUCK_16T"     # E.g., Multi-axle 10-wheeler (160 Quintals)


class LogisticsStatus(str, Enum):
    PENDING = "PENDING"
    BOOKED = "BOOKED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================
# Vehicle Class Specification
# ==========================================

class VehicleClassDetail(BaseModel):
    vehicle_type: VehicleType
    display_name: str
    max_capacity_quintals: float = Field(..., gt=0.0)
    base_fare_inr: float = Field(..., ge=0.0)
    per_km_rate_inr: float = Field(..., gt=0.0)


# ==========================================
# Route & Freight Quote Schemas
# ==========================================

class LogisticsQuoteRequest(BaseModel):
    origin_address: str = Field(..., min_length=2, max_length=250, description="Farm origin or collection center")
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lng: float = Field(..., ge=-180.0, le=180.0)
    destination_address: str = Field(..., min_length=2, max_length=250, description="Destination Mandi or Buyer warehouse")
    destination_lat: float = Field(..., ge=-90.0, le=90.0)
    destination_lng: float = Field(..., ge=-180.0, le=180.0)
    cargo_weight_quintals: float = Field(..., gt=0.0, description="Total load weight in Quintals")
    is_consolidated_pickup: bool = Field(default=False, description="Whether route combines multi-farm pickup")


class LogisticsQuoteResponse(BaseModel):
    distance_km: float = Field(..., ge=0.0, description="True road distance (e.g. via OSRM / OpenStreetMap)")
    estimated_duration_hours: float = Field(..., ge=0.0)
    recommended_vehicle: VehicleType
    number_of_vehicles_required: int = Field(default=1, ge=1)
    base_transport_cost: float = Field(..., ge=0.0)
    fuel_surcharge: float = Field(default=0.0, ge=0.0)
    loading_unloading_cost: float = Field(default=0.0, ge=0.0)
    total_freight_cost: float = Field(..., ge=0.0, description="Total line-item logistics charge")
    freight_cost_per_quintal: float = Field(..., ge=0.0, description="Freight cost divided by load weight")
    consolidation_savings: float = Field(default=0.0, ge=0.0, description="Savings achieved via pooled bulk transport")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Logistics Booking & Tracking
# ==========================================

class LogisticsBookingCreate(BaseModel):
    transaction_id: int
    vehicle_type: VehicleType
    origin_address: str
    destination_address: str
    pickup_contact_name: str
    pickup_contact_phone: str
    scheduled_pickup_time: datetime


class LogisticsResponse(BaseModel):
    id: int
    transaction_id: int
    vehicle_type: VehicleType
    origin_address: str
    destination_address: str
    distance_km: float
    estimated_cost: float
    actual_cost: Optional[float] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    vehicle_number: Optional[str] = None
    status: LogisticsStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
