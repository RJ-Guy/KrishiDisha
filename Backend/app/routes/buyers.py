"""
Buyers, Institutional Procurement Tenders, and Multi-Factor Reverse Matching
Router for KrishiDisha.
Supports buyer directory discovery, institutional bulk tenders,
hard-constraint filtering, and multi-factor weighted match scoring.
"""

import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.buyer_schema import (
    BuyerCategory,
    RequirementStatus,
    BuyerResponse,
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
    BuyerRequirementResponse,
    BuyerMatchScoreBreakdown,
    BuyerMatchResult,
    BuyerMatchQuery,
)
from app.schemas.lot_schema import QualityGrade
from app.schemas.auth_schema import UserRole

# Dependencies
from app.routes.auth import get_db, get_current_user, require_role

# Distance Helper
from app.routes.market import calculate_road_distance_km

router = APIRouter(prefix="/buyers", tags=["Buyers & Reverse Marketplace"])

# ==========================================
# In-Memory Demonstration Data
# ==========================================
_MOCK_BUYERS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "user_id": 3,
        "company_name": "ITC Limited Agri Business (e-Choupal)",
        "gst_no": "23AAACI1681G1Z0",
        "trade_license": "TL-MP-IND-88219",
        "buyer_category": BuyerCategory.INSTITUTIONAL,
        "reliability_score": 98.5,
        "verified": True,
        "operating_states": ["Madhya Pradesh", "Rajasthan", "Maharashtra"],
        "on_time_payment_rate_pct": 99.2,
        "total_deals_completed": 1420,
        "created_at": datetime(2024, 1, 15, tzinfo=timezone.utc),
    },
    2: {
        "id": 2,
        "user_id": 6,
        "company_name": "Adani Wilmar Ltd (Fortune Agro Hub)",
        "gst_no": "23AABCA1234F1Z5",
        "trade_license": "TL-MP-UJJ-44102",
        "buyer_category": BuyerCategory.PROCESSOR,
        "reliability_score": 96.0,
        "verified": True,
        "operating_states": ["Madhya Pradesh", "Gujarat"],
        "on_time_payment_rate_pct": 97.5,
        "total_deals_completed": 980,
        "created_at": datetime(2024, 3, 10, tzinfo=timezone.utc),
    },
    3: {
        "id": 3,
        "user_id": 7,
        "company_name": "Cargill India Pvt Ltd (Malwa Procurement)",
        "gst_no": "23AABCC5678K1Z2",
        "trade_license": "TL-MP-DEW-99120",
        "buyer_category": BuyerCategory.EXPORTER,
        "reliability_score": 94.0,
        "verified": True,
        "operating_states": ["Madhya Pradesh", "Punjab", "Haryana"],
        "on_time_payment_rate_pct": 95.8,
        "total_deals_completed": 640,
        "created_at": datetime(2024, 5, 20, tzinfo=timezone.utc),
    },
    4: {
        "id": 4,
        "user_id": 8,
        "company_name": "Malwa Modern Roller Flour Mills",
        "gst_no": "23AABCM3312J1Z8",
        "trade_license": "TL-MP-UJJ-22019",
        "buyer_category": BuyerCategory.PROCESSOR,
        "reliability_score": 91.5,
        "verified": True,
        "operating_states": ["Madhya Pradesh"],
        "on_time_payment_rate_pct": 93.0,
        "total_deals_completed": 310,
        "created_at": datetime(2024, 8, 5, tzinfo=timezone.utc),
    },
}

_MOCK_REQUIREMENTS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "buyer_id": 1,
        "company_name": "ITC Limited Agri Business (e-Choupal)",
        "buyer_reliability_score": 98.5,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati Premium",
        "required_quantity_quintals": 1000.0,
        "max_price_per_quintal": 2680.0,
        "min_grade": QualityGrade.GRADE_A,
        "max_moisture_pct": 11.5,
        "delivery_location_name": "ITC Procurement Hub, Dewas Naka, Indore, MP",
        "delivery_location_lat": 22.7712,
        "delivery_location_lng": 75.8941,
        "delivery_window_start": date.today(),
        "delivery_window_end": date.today() + timedelta(days=30),
        "special_conditions": "Moisture must be <= 11.5%. Payment within 24 hours of digital weighment slip.",
        "status": RequirementStatus.OPEN,
        "fulfilled_quantity_quintals": 320.0,
        "created_at": datetime.now(timezone.utc) - timedelta(days=5),
        "expiry_date": date.today() + timedelta(days=30),
    },
    2: {
        "id": 2,
        "buyer_id": 2,
        "company_name": "Adani Wilmar Ltd (Fortune Agro Hub)",
        "buyer_reliability_score": 96.0,
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "variety": "JS-335",
        "required_quantity_quintals": 2500.0,
        "max_price_per_quintal": 4750.0,
        "min_grade": QualityGrade.FAQ,
        "max_moisture_pct": 12.0,
        "delivery_location_name": "Adani Wilmar Crushing Plant, Industrial Area, Ujjain, MP",
        "delivery_location_lat": 23.1812,
        "delivery_location_lng": 75.8105,
        "delivery_window_start": date.today(),
        "delivery_window_end": date.today() + timedelta(days=20),
        "special_conditions": "Minimum lot size 50 Quintals. FPO aggregated lots prioritized.",
        "status": RequirementStatus.OPEN,
        "fulfilled_quantity_quintals": 950.0,
        "created_at": datetime.now(timezone.utc) - timedelta(days=3),
        "expiry_date": date.today() + timedelta(days=20),
    },
    3: {
        "id": 3,
        "buyer_id": 4,
        "company_name": "Malwa Modern Roller Flour Mills",
        "buyer_reliability_score": 91.5,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "required_quantity_quintals": 400.0,
        "max_price_per_quintal": 2620.0,
        "min_grade": QualityGrade.GRADE_A,
        "max_moisture_pct": 12.0,
        "delivery_location_name": "Nagda Road Processing Mill, Badnagar, Ujjain, MP",
        "delivery_location_lat": 23.0710,
        "delivery_location_lng": 75.3920,
        "delivery_window_start": date.today(),
        "delivery_window_end": date.today() + timedelta(days=15),
        "special_conditions": "Direct gate delivery. Spot cash settlement or RTGS.",
        "status": RequirementStatus.OPEN,
        "fulfilled_quantity_quintals": 110.0,
        "created_at": datetime.now(timezone.utc) - timedelta(days=2),
        "expiry_date": date.today() + timedelta(days=15),
    },
}


# ==========================================
# Route Handlers
# ==========================================

@router.get("", response_model=List[BuyerResponse], summary="List Verified Institutional Buyers")
def list_buyers(
    category: Optional[BuyerCategory] = Query(None, description="Filter by buyer category"),
    min_reliability: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum reliability score"),
):
    """Browse verified institutional buyers, processors, and exporters."""
    results = []
    for b in _MOCK_BUYERS.values():
        if category and b["buyer_category"] != category:
            continue
        if min_reliability and b["reliability_score"] < min_reliability:
            continue
        results.append(BuyerResponse(**b))
    return results


@router.get("/requirements", response_model=List[BuyerRequirementResponse], summary="Browse Institutional Bulk Tenders")
def list_requirements(
    commodity_id: Optional[int] = Query(None),
    status_filter: Optional[RequirementStatus] = Query(RequirementStatus.OPEN, alias="status"),
):
    """Browse active reverse procurement tenders posted by institutional buyers."""
    results = []
    for req in _MOCK_REQUIREMENTS.values():
        if commodity_id and req["commodity_id"] != commodity_id:
            continue
        if status_filter and req["status"] != status_filter:
            continue
        results.append(BuyerRequirementResponse(**req))
    return results


@router.get("/requirements/{req_id}", response_model=BuyerRequirementResponse, summary="Get Bulk Tender by ID")
def get_requirement(req_id: int):
    """Retrieve full procurement tender requirements."""
    if req_id not in _MOCK_REQUIREMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement tender requirement not found")
    return BuyerRequirementResponse(**_MOCK_REQUIREMENTS[req_id])


@router.post("/requirements", response_model=BuyerRequirementResponse, status_code=status.HTTP_201_CREATED, summary="Post Bulk Procurement Tender")
def post_requirement(
    payload: BuyerRequirementCreate,
    current_user: Any = Depends(require_role(UserRole.BUYER, UserRole.ADMIN)),
    db: Optional[Session] = Depends(get_db),
):
    """Post an institutional demand requirement for reverse matching."""
    user_id = getattr(current_user, "id", None) or current_user.get("id", 3)
    company = "Institutional Buyer"
    buyer_id = 1
    reliability = 98.0

    for bid, bdata in _MOCK_BUYERS.items():
        if bdata.get("user_id") == user_id:
            buyer_id = bid
            company = bdata["company_name"]
            reliability = bdata["reliability_score"]
            break

    new_id = max(_MOCK_REQUIREMENTS.keys(), default=0) + 1
    new_req = {
        "id": new_id,
        "buyer_id": buyer_id,
        "company_name": company,
        "buyer_reliability_score": reliability,
        "commodity_id": payload.commodity_id,
        "commodity_name": payload.commodity_name or "Agricultural Commodity",
        "variety": payload.variety,
        "required_quantity_quintals": payload.required_quantity_quintals,
        "max_price_per_quintal": payload.max_price_per_quintal,
        "min_grade": payload.min_grade,
        "max_moisture_pct": payload.max_moisture_pct,
        "delivery_location_name": payload.delivery_location_name,
        "delivery_location_lat": payload.delivery_location_lat,
        "delivery_location_lng": payload.delivery_location_lng,
        "delivery_window_start": payload.delivery_window_start,
        "delivery_window_end": payload.delivery_window_end,
        "special_conditions": payload.special_conditions,
        "status": RequirementStatus.OPEN,
        "fulfilled_quantity_quintals": 0.0,
        "created_at": datetime.now(timezone.utc),
        "expiry_date": payload.delivery_window_end,
    }
    _MOCK_REQUIREMENTS[new_id] = new_req
    return BuyerRequirementResponse(**new_req)


@router.put("/requirements/{req_id}", response_model=BuyerRequirementResponse, summary="Update Procurement Tender")
def update_requirement(
    req_id: int,
    payload: BuyerRequirementUpdate,
    current_user: Any = Depends(require_role(UserRole.BUYER, UserRole.ADMIN)),
):
    """Update procurement tender volume, price budget, or status."""
    if req_id not in _MOCK_REQUIREMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

    req = _MOCK_REQUIREMENTS[req_id]
    if payload.required_quantity_quintals is not None:
        req["required_quantity_quintals"] = payload.required_quantity_quintals
    if payload.max_price_per_quintal is not None:
        req["max_price_per_quintal"] = payload.max_price_per_quintal
    if payload.status is not None:
        req["status"] = payload.status
    if payload.max_moisture_pct is not None:
        req["max_moisture_pct"] = payload.max_moisture_pct

    return BuyerRequirementResponse(**req)


@router.post("/match", response_model=List[BuyerMatchResult], summary="Run Multi-Factor Buyer Matching Algorithm")
def match_buyers(payload: BuyerMatchQuery):
    """
    Reverse Marketplace Buyer Matching Engine:
    Evaluates hard constraints (commodity, moisture <= threshold, distance),
    then computes a weighted multi-factor scoring matrix:
    Score = w1*Price + w2*Distance + w3*Quality + w4*Reliability + w5*Volume.
    """
    matches: List[BuyerMatchResult] = []

    for req in _MOCK_REQUIREMENTS.values():
        if req["status"] != RequirementStatus.OPEN:
            continue

        # Hard Constraint 1: Commodity ID
        if req["commodity_id"] != payload.commodity_id:
            continue

        # Distance calculation
        dist_km = calculate_road_distance_km(
            payload.origin_lat, payload.origin_lng,
            req["delivery_location_lat"], req["delivery_location_lng"]
        )

        # Hard Constraint 2: Maximum Distance
        max_dist = payload.max_distance_km or 250.0
        if dist_km > max_dist:
            continue

        # Hard Constraint 3: Moisture Threshold
        moisture_passed = payload.moisture_pct <= req["max_moisture_pct"]
        if not moisture_passed:
            continue

        # Scoring weights
        # w1: Price (35%), w2: Distance (20%), w3: Quality fit (15%), w4: Reliability (20%), w5: Volume (10%)
        # Price score: Ratio of offered price to max baseline (capped at 100)
        price_offered = req["max_price_per_quintal"]
        price_score = min(100.0, (price_offered / 2700.0) * 100.0)

        # Distance score: Shorter distance gets higher score
        dist_score = max(0.0, 100.0 - (dist_km / 2.5))

        # Quality fit score: Extra points for being below max moisture
        moisture_margin = req["max_moisture_pct"] - payload.moisture_pct
        quality_score = min(100.0, 85.0 + (moisture_margin * 7.5))

        # Reliability score from buyer history
        rel_score = req["buyer_reliability_score"]

        # Volume compatibility score
        rem_vol = req["required_quantity_quintals"] - req["fulfilled_quantity_quintals"]
        vol_score = min(100.0, (min(payload.quantity_quintals, rem_vol) / payload.quantity_quintals) * 100.0)

        overall = (
            0.35 * price_score
            + 0.20 * dist_score
            + 0.15 * quality_score
            + 0.20 * rel_score
            + 0.10 * vol_score
        )
        overall = round(overall, 1)

        # Economics
        est_freight_per_q = max(20.0, round(dist_km * 0.40, 2))
        est_net_realization = round(price_offered - est_freight_per_q - 10.0, 2)

        explanation = (
            f"{overall:.0f}% Match: Offered price ₹{price_offered:.0f}/Q, {dist_km:.1f} km distance, "
            f"{rel_score:.1f}% buyer reliability track record, moisture {payload.moisture_pct:.1f}% compliant."
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
                requirement_id=req["id"],
                offered_price_per_quintal=price_offered,
                distance_km=dist_km,
                overall_match_score=overall,
                score_breakdown=breakdown,
                human_readable_explanation=explanation,
                estimated_transport_cost=round(est_freight_per_q * payload.quantity_quintals, 2),
                estimated_net_realization=est_net_realization,
                is_hard_filter_passed=True,
                disqualification_reason=None,
            )
        )

    # Sort descending by overall match score
    matches.sort(key=lambda m: m.overall_match_score, reverse=True)
    return matches


@router.get("/{buyer_id}", response_model=BuyerResponse, summary="Get Buyer Profile by ID")
def get_buyer(buyer_id: int):
    """Retrieve verified buyer profile, category, and historical reliability metrics."""
    if buyer_id not in _MOCK_BUYERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer profile not found")
    return BuyerResponse(**_MOCK_BUYERS[buyer_id])
