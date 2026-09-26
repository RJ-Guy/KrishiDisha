"""
Buyer Matching and Reverse Marketplace Heuristics Engine for KrishiDisha.
Applies hard quality/geographic constraint filtering, followed by a multi-factor
weighted scoring matrix:
Score = w1*Price + w2*Distance + w3*Quality + w4*Reliability + w5*Volume.
"""

from typing import Optional, List, Dict, Any
from app.schemas.buyer_schema import (
    BuyerMatchScoreBreakdown,
    BuyerMatchResult,
    BuyerMatchQuery,
    RequirementStatus,
)
from app.schemas.lot_schema import QualityGrade
from app.services.logistics_service import calculate_haversine_road_distance

# Weights for multi-factor scoring matrix
W_PRICE = 0.35
W_DISTANCE = 0.20
W_QUALITY = 0.15
W_RELIABILITY = 0.20
W_VOLUME = 0.10

# Baseline Reference Institutional Requirements
DEFAULT_BUYER_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "buyer_id": 1,
        "company_name": "ITC Limited Agri Business (e-Choupal)",
        "buyer_reliability_score": 98.5,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "required_quantity_quintals": 1000.0,
        "fulfilled_quantity_quintals": 320.0,
        "max_price_per_quintal": 2680.0,
        "min_grade": QualityGrade.GRADE_A,
        "max_moisture_pct": 11.5,
        "delivery_location_lat": 22.7712,
        "delivery_location_lng": 75.8941,
        "status": RequirementStatus.OPEN,
    },
    {
        "id": 2,
        "buyer_id": 2,
        "company_name": "Adani Wilmar Ltd (Fortune Agro Hub)",
        "buyer_reliability_score": 96.0,
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "variety": "JS-335",
        "required_quantity_quintals": 2500.0,
        "fulfilled_quantity_quintals": 950.0,
        "max_price_per_quintal": 4750.0,
        "min_grade": QualityGrade.FAQ,
        "max_moisture_pct": 12.0,
        "delivery_location_lat": 23.1812,
        "delivery_location_lng": 75.8105,
        "status": RequirementStatus.OPEN,
    },
    {
        "id": 3,
        "buyer_id": 4,
        "company_name": "Malwa Modern Roller Flour Mills",
        "buyer_reliability_score": 91.5,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "required_quantity_quintals": 400.0,
        "fulfilled_quantity_quintals": 110.0,
        "max_price_per_quintal": 2620.0,
        "min_grade": QualityGrade.GRADE_A,
        "max_moisture_pct": 12.0,
        "delivery_location_lat": 23.0710,
        "delivery_location_lng": 75.3920,
        "status": RequirementStatus.OPEN,
    },
]


def match_lot_to_buyers(
    commodity_id: int,
    quantity_quintals: float,
    moisture_pct: float,
    quality_grade: QualityGrade,
    origin_lat: float,
    origin_lng: float,
    max_distance_km: float = 250.0,
    variety: Optional[str] = None,
    available_requirements: Optional[List[Dict[str, Any]]] = None,
) -> List[BuyerMatchResult]:
    """
    Evaluates institutional buyers against an active lot:
    1. Hard constraints: commodity match, moisture <= max_moisture_pct, road distance <= max_distance_km.
    2. Multi-factor scoring: price (35%), distance (20%), quality fit (15%), reliability (20%), volume (10%).
    """
    reqs = available_requirements or DEFAULT_BUYER_REQUIREMENTS
    matches: List[BuyerMatchResult] = []

    for req in reqs:
        # Check requirement status
        req_status = req.get("status", RequirementStatus.OPEN)
        if req_status != RequirementStatus.OPEN and getattr(req_status, "value", req_status) != "OPEN":
            continue

        # Hard Constraint 1: Commodity ID
        if req["commodity_id"] != commodity_id:
            continue

        # Road distance calculation
        dest_lat = req["delivery_location_lat"]
        dest_lng = req["delivery_location_lng"]
        dist_km = calculate_haversine_road_distance(origin_lat, origin_lng, dest_lat, dest_lng)

        # Hard Constraint 2: Maximum Distance
        if dist_km > max_distance_km:
            continue

        # Hard Constraint 3: Moisture Threshold
        req_max_moisture = float(req.get("max_moisture_pct", 12.0))
        if moisture_pct > req_max_moisture:
            continue

        # ------------------------------------
        # Multi-Factor Weighted Scoring
        # ------------------------------------
        # 1. Price Score: Ratio of offered price to benchmark 2700 for wheat, 4800 for soybean
        price_offered = float(req["max_price_per_quintal"])
        price_baseline = 2700.0 if commodity_id == 1 else 4800.0
        price_score = min(100.0, (price_offered / price_baseline) * 100.0)

        # 2. Distance Score: Proximity efficiency (closer = higher score)
        dist_score = max(0.0, min(100.0, 100.0 - (dist_km / 2.5)))

        # 3. Quality Fit Score: Reward for lower moisture than required
        moisture_margin = req_max_moisture - moisture_pct
        quality_score = min(100.0, 85.0 + (moisture_margin * 7.5))

        # 4. Reliability Score from buyer track record
        rel_score = float(req.get("buyer_reliability_score", 95.0))

        # 5. Volume Compatibility Score
        rem_vol = float(req["required_quantity_quintals"]) - float(req.get("fulfilled_quantity_quintals", 0.0))
        vol_score = min(100.0, (min(quantity_quintals, rem_vol) / quantity_quintals) * 100.0) if quantity_quintals > 0 else 0.0

        overall = (
            W_PRICE * price_score
            + W_DISTANCE * dist_score
            + W_QUALITY * quality_score
            + W_RELIABILITY * rel_score
            + W_VOLUME * vol_score
        )
        overall = round(overall, 1)

        # Logistics and Net Realization projection
        est_freight_per_q = max(20.0, round(dist_km * 0.40, 2))
        est_transport_total = round(est_freight_per_q * quantity_quintals, 2)
        est_net_realization = round(price_offered - est_freight_per_q - 10.0, 2)

        explanation = (
            f"{overall:.0f}% Match: Offered price ₹{price_offered:,.0f}/Q, {dist_km:.1f} km away, "
            f"{rel_score:.1f}% buyer reliability track record, moisture {moisture_pct:.1f}% compliant."
        )

        breakdown = BuyerMatchScoreBreakdown(
            price_score=round(price_score, 1),
            distance_score=round(dist_score, 1),
            quality_fit_score=round(quality_score, 1),
            reliability_score=round(rel_score, 1),
            volume_compatibility_score=round(vol_score, 1),
        )

        matches.append(
            BuyerMatchResult(
                buyer_id=req["buyer_id"],
                company_name=req["company_name"],
                requirement_id=req.get("id"),
                offered_price_per_quintal=price_offered,
                distance_km=dist_km,
                overall_match_score=overall,
                score_breakdown=breakdown,
                human_readable_explanation=explanation,
                estimated_transport_cost=est_transport_total,
                estimated_net_realization=est_net_realization,
                is_hard_filter_passed=True,
                disqualification_reason=None,
            )
        )

    # Sort descending by overall match score
    matches.sort(key=lambda m: m.overall_match_score, reverse=True)
    return matches
