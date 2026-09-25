"""
Logistics and Route Tariff Calculation Engine for KrishiDisha.
Provides true road distance estimation, vehicle tier classification (1.5T, 5T, 16T),
freight rate computation, and bulk transport consolidation savings analysis.
"""

import math
from typing import Dict, Any, Tuple
from app.schemas.logistics_schema import (
    VehicleType,
    LogisticsQuoteResponse,
)

# Vehicle specifications & tariffs
VEHICLE_CONFIGS: Dict[VehicleType, Dict[str, Any]] = {
    VehicleType.MINI_TRUCK_1_5T: {
        "display_name": "Mini Truck (Tata Ace / Mahindra Bolero)",
        "capacity_quintals": 15.0,
        "base_fare": 650.0,
        "per_km_rate": 14.0,
        "loading_rate_per_q": 5.0,
    },
    VehicleType.MEDIUM_TRUCK_5T: {
        "display_name": "Medium Truck (Eicher 14-ft / 5 Tonne)",
        "capacity_quintals": 50.0,
        "base_fare": 1400.0,
        "per_km_rate": 24.0,
        "loading_rate_per_q": 4.5,
    },
    VehicleType.HEAVY_TRUCK_16T: {
        "display_name": "Heavy Truck (10-Wheeler / 16 Tonne)",
        "capacity_quintals": 160.0,
        "base_fare": 3200.0,
        "per_km_rate": 42.0,
        "loading_rate_per_q": 4.0,
    },
}


def calculate_haversine_road_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    road_factor: float = 1.28,
) -> float:
    """
    Computes geospatial great-circle distance multiplied by the Indian rural
    road winding factor (default 1.28) to closely approximate real road distance.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    r = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = r * c * road_factor

    return round(max(1.0, distance), 1)


def select_vehicle_fleet(weight_quintals: float) -> Tuple[VehicleType, int]:
    """
    Selects optimal vehicle classification and number of vehicles required.
    """
    if weight_quintals <= 15.0:
        return VehicleType.MINI_TRUCK_1_5T, 1
    elif weight_quintals <= 50.0:
        return VehicleType.MEDIUM_TRUCK_5T, 1
    elif weight_quintals <= 160.0:
        return VehicleType.HEAVY_TRUCK_16T, 1
    else:
        # Multi-vehicle heavy fleet
        num_vehicles = math.ceil(weight_quintals / 160.0)
        return VehicleType.HEAVY_TRUCK_16T, num_vehicles


def compute_freight_quote(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    cargo_weight_quintals: float,
    is_consolidated: bool = False,
) -> LogisticsQuoteResponse:
    """
    Computes calibrated road distance, vehicle recommendation, line-item freight costs,
    and pooling consolidation savings.
    """
    if cargo_weight_quintals <= 0:
        raise ValueError("Cargo weight must be greater than zero")

    dist_km = calculate_haversine_road_distance(origin_lat, origin_lng, dest_lat, dest_lng)
    est_hours = round(max(0.5, dist_km / 35.0), 1)  # Avg 35 km/h for agricultural transit

    v_type, num_vehicles = select_vehicle_fleet(cargo_weight_quintals)
    cfg = VEHICLE_CONFIGS[v_type]

    base_transport = round((cfg["base_fare"] + (dist_km * cfg["per_km_rate"])) * num_vehicles, 2)
    fuel_surcharge = round(base_transport * 0.08, 2)  # 8% standard fuel adjustment
    loading_cost = round(cargo_weight_quintals * cfg["loading_rate_per_q"], 2)

    total_cost = round(base_transport + fuel_surcharge + loading_cost, 2)
    per_q = round(total_cost / cargo_weight_quintals, 2)

    # Consolidation savings calculation:
    # If pooling 45+ Quintals, compare against 3+ separate mini truck trips
    consolidation_savings = 0.0
    if cargo_weight_quintals >= 30.0 or is_consolidated:
        mini_cfg = VEHICLE_CONFIGS[VehicleType.MINI_TRUCK_1_5T]
        mini_trips = math.ceil(cargo_weight_quintals / mini_cfg["capacity_quintals"])
        equivalent_mini_cost = (mini_cfg["base_fare"] + dist_km * mini_cfg["per_km_rate"]) * mini_trips
        consolidation_savings = max(0.0, round(equivalent_mini_cost - total_cost, 2))

    return LogisticsQuoteResponse(
        distance_km=dist_km,
        estimated_duration_hours=est_hours,
        recommended_vehicle=v_type,
        number_of_vehicles_required=num_vehicles,
        base_transport_cost=base_transport,
        fuel_surcharge=fuel_surcharge,
        loading_unloading_cost=loading_cost,
        total_freight_cost=total_cost,
        freight_cost_per_quintal=per_q,
        consolidation_savings=consolidation_savings,
    )
