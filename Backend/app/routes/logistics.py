"""
Logistics, Fleet Dispatch, Freight Tariff Calculation, and Nearby Storage
Router for KrishiDisha.
Supports vehicle classification (1.5T Mini, 5T Medium, 16T Heavy),
road distance calculation, freight quote generation with consolidation savings,
and warehousing discovery.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.logistics_schema import (
    VehicleType,
    LogisticsStatus,
    VehicleClassDetail,
    LogisticsQuoteRequest,
    LogisticsQuoteResponse,
    LogisticsBookingCreate,
    LogisticsResponse,
)

# Dependencies
from app.routes.auth import get_db, get_current_user

# Distance Helper
from app.routes.market import calculate_road_distance_km

router = APIRouter(prefix="/logistics", tags=["Logistics & Storage"])

# ==========================================
# Vehicle Class Specs
# ==========================================
VEHICLE_SPECS: Dict[VehicleType, Dict[str, Any]] = {
    VehicleType.MINI_TRUCK_1_5T: {
        "display_name": "Mini Truck (Tata Ace / Bolero Maxi)",
        "capacity_quintals": 15.0,
        "base_fare": 650.0,
        "per_km_rate": 14.0,
    },
    VehicleType.MEDIUM_TRUCK_5T: {
        "display_name": "Medium Truck (Eicher 14-ft / 5 Tonne)",
        "capacity_quintals": 50.0,
        "base_fare": 1400.0,
        "per_km_rate": 24.0,
    },
    VehicleType.HEAVY_TRUCK_16T: {
        "display_name": "Heavy Truck (10-Wheeler / 16 Tonne)",
        "capacity_quintals": 160.0,
        "base_fare": 3200.0,
        "per_km_rate": 42.0,
    },
}

_MOCK_BOOKINGS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "transaction_id": 1,
        "vehicle_type": VehicleType.MEDIUM_TRUCK_5T,
        "origin_address": "Village Nagda, Ujjain, MP",
        "destination_address": "ITC Procurement Hub, Dewas Naka, Indore, MP",
        "distance_km": 58.5,
        "estimated_cost": 2800.0,
        "actual_cost": None,
        "driver_name": "Balwant Singh",
        "driver_phone": "9826012345",
        "vehicle_number": "MP-13-GA-4589",
        "status": LogisticsStatus.BOOKED,
        "created_at": datetime.now(timezone.utc),
    }
}

_MOCK_STORAGE_FACILITIES = [
    {
        "id": 1,
        "facility_name": "MP State Warehousing & Logistics Corp (MPSWC) - Ujjain Hub",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "daily_cost_per_quintal": 0.45,
        "capacity_quintals": 45000.0,
        "available_capacity_quintals": 12800.0,
        "latitude": 23.1850,
        "longitude": 75.8010,
        "accredited_wdra": True,
    },
    {
        "id": 2,
        "facility_name": "National Collateral Management Services (NCML) Cold Chain",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "daily_cost_per_quintal": 0.70,
        "capacity_quintals": 25000.0,
        "available_capacity_quintals": 6400.0,
        "latitude": 22.7650,
        "longitude": 75.8850,
        "accredited_wdra": True,
    },
    {
        "id": 3,
        "facility_name": "Nagda Rural Agri Cold Storage & Silos",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "daily_cost_per_quintal": 0.40,
        "capacity_quintals": 10000.0,
        "available_capacity_quintals": 3100.0,
        "latitude": 23.4480,
        "longitude": 75.4250,
        "accredited_wdra": False,
    },
]


def calculate_quote(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    weight_q: float,
    is_consolidated: bool = False,
) -> LogisticsQuoteResponse:
    """Core freight tariff and vehicle recommendation algorithm."""
    dist_km = calculate_road_distance_km(origin_lat, origin_lng, dest_lat, dest_lng)
    est_hours = round(max(0.5, dist_km / 35.0), 1)  # Avg 35 km/h for agricultural transit

    # Vehicle selection heuristic
    if weight_q <= 15.0:
        v_type = VehicleType.MINI_TRUCK_1_5T
        num_v = 1
    elif weight_q <= 50.0:
        v_type = VehicleType.MEDIUM_TRUCK_5T
        num_v = 1
    elif weight_q <= 160.0:
        v_type = VehicleType.HEAVY_TRUCK_16T
        num_v = 1
    else:
        v_type = VehicleType.HEAVY_TRUCK_16T
        num_v = math.ceil(weight_q / 160.0)

    spec = VEHICLE_SPECS[v_type]
    base_cost = (spec["base_fare"] + (dist_km * spec["per_km_rate"])) * num_v
    fuel_surcharge = round(base_cost * 0.08, 2)
    loading_unloading = round(weight_q * 4.5, 2)  # ₹4.5 per quintal loading/unloading
    total_cost = round(base_cost + fuel_surcharge + loading_unloading, 2)
    per_q = round(total_cost / weight_q, 2) if weight_q > 0 else 0.0

    # Consolidation savings calculation
    # If using 1 medium truck instead of 3 mini trucks, or pooling with others:
    savings = 0.0
    if weight_q >= 40.0:
        equivalent_mini_cost = (VEHICLE_SPECS[VehicleType.MINI_TRUCK_1_5T]["base_fare"] + dist_km * 14.0) * math.ceil(weight_q / 15.0)
        savings = max(0.0, round(equivalent_mini_cost - total_cost, 2))

    return LogisticsQuoteResponse(
        distance_km=dist_km,
        estimated_duration_hours=est_hours,
        recommended_vehicle=v_type,
        number_of_vehicles_required=num_v,
        base_transport_cost=round(base_cost, 2),
        fuel_surcharge=fuel_surcharge,
        loading_unloading_cost=loading_unloading,
        total_freight_cost=total_cost,
        freight_cost_per_quintal=per_q,
        consolidation_savings=savings,
    )


# ==========================================
# Route Handlers
# ==========================================

@router.post("/quote", response_model=LogisticsQuoteResponse, summary="Calculate Freight & Routing Quote (POST)")
def get_quote_post(payload: LogisticsQuoteRequest):
    """
    Compute OSRM-calibrated road distance, transit time, vehicle tier recommendation,
    line-item freight quote, and pooled transport savings.
    """
    return calculate_quote(
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        dest_lat=payload.destination_lat,
        dest_lng=payload.destination_lng,
        weight_q=payload.cargo_weight_quintals,
        is_consolidated=payload.is_consolidated_pickup,
    )


@router.get("/estimate", response_model=LogisticsQuoteResponse, summary="Calculate Freight & Routing Quote (GET)")
def get_quote_get(
    origin_lat: float = Query(..., ge=-90.0, le=90.0),
    origin_lng: float = Query(..., ge=-180.0, le=180.0),
    destination_lat: float = Query(..., ge=-90.0, le=90.0),
    destination_lng: float = Query(..., ge=-180.0, le=180.0),
    cargo_weight_quintals: float = Query(..., gt=0.0),
):
    """Query parameter version of freight quote calculation for interactive frontend maps."""
    return calculate_quote(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=destination_lat,
        dest_lng=destination_lng,
        weight_q=cargo_weight_quintals,
    )


@router.post("/book", response_model=LogisticsResponse, status_code=status.HTTP_201_CREATED, summary="Book Freight Vehicle")
def book_transport(payload: LogisticsBookingCreate, current_user: Any = Depends(get_current_user)):
    """Book dispatch vehicle for an active transaction."""
    new_id = max(_MOCK_BOOKINGS.keys(), default=0) + 1
    booking = {
        "id": new_id,
        "transaction_id": payload.transaction_id,
        "vehicle_type": payload.vehicle_type,
        "origin_address": payload.origin_address,
        "destination_address": payload.destination_address,
        "distance_km": 45.0,
        "estimated_cost": 2250.0,
        "actual_cost": None,
        "driver_name": "Kripal Singh",
        "driver_phone": payload.pickup_contact_phone,
        "vehicle_number": "MP-09-AB-1234",
        "status": LogisticsStatus.BOOKED,
        "created_at": datetime.now(timezone.utc),
    }
    _MOCK_BOOKINGS[new_id] = booking
    return LogisticsResponse(**booking)


@router.get("/{booking_id}", response_model=LogisticsResponse, summary="Get Transport Booking Details")
def get_booking(booking_id: int):
    """Retrieve logistics booking details, vehicle details, and transit stage."""
    if booking_id not in _MOCK_BOOKINGS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logistics booking not found")
    return LogisticsResponse(**_MOCK_BOOKINGS[booking_id])


@router.get("/storage/nearby", summary="Discover Agricultural Warehouses & Cold Storages")
def list_nearby_storage(
    user_lat: float = Query(..., ge=-90.0, le=90.0),
    user_lng: float = Query(..., ge=-180.0, le=180.0),
    max_distance_km: Optional[float] = Query(50.0, gt=0.0),
):
    """Query licensed warehouses and cold storage units by distance and daily rental tariff."""
    results = []
    for facility in _MOCK_STORAGE_FACILITIES:
        dist = calculate_road_distance_km(user_lat, user_lng, facility["latitude"], facility["longitude"])
        if max_distance_km and dist > max_distance_km:
            continue
        results.append({**facility, "distance_km": dist})
    results.sort(key=lambda x: x["distance_km"])
    return results
