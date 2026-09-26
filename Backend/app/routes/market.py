"""
Market Intelligence, Mandi Prices, Historical Price Trends, and
MSP Procurement Router for KrishiDisha.
Supports multi-mandi price discovery, arrival volume tracking,
historical price series with moving averages, and net realization previews.
"""

import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.market_schema import (
    PriceTrend,
    MandiBase,
    MandiCreate,
    MandiResponse,
    MarketPriceCreate,
    MarketPriceResponse,
    MandiPriceFilter,
    PriceTrendPoint,
    HistoricalPriceQuery,
    MarketTrendsResponse,
    ProcurementOptionCreate,
    ProcurementOptionResponse,
)

# Dependencies
from app.routes.auth import get_db

# Models
try:
    from app.models.market import Commodity, Market, MarketPrice, ProcurementOption
except ImportError:
    Commodity = Market = MarketPrice = ProcurementOption = None

router = APIRouter(prefix="/market", tags=["Market Intelligence"])

# ==========================================
# Distance Calculation Helper
# ==========================================
def calculate_road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance multiplied by winding road factor (1.28)."""
    r = 6371.0  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c * 1.28, 1)


# ==========================================
# In-Memory Demonstration Data
# ==========================================
_MOCK_MANDIS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "market_name": "Ujjain APMC Mandi (Chimanganj Mandi)",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "latitude": 23.2014,
        "longitude": 75.7947,
        "is_apmc": True,
        "operating_days": "Mon-Sat",
    },
    {
        "id": 2,
        "market_name": "Indore Laxmi Bai Nagar APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "latitude": 22.7533,
        "longitude": 75.8637,
        "is_apmc": True,
        "operating_days": "Mon-Sat",
    },
    {
        "id": 3,
        "market_name": "Dewas APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Dewas",
        "latitude": 22.9676,
        "longitude": 76.0534,
        "is_apmc": True,
        "operating_days": "Mon-Sat",
    },
    {
        "id": 4,
        "market_name": "Badnagar Sub-Mandi Yard",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "latitude": 23.0634,
        "longitude": 75.3857,
        "is_apmc": True,
        "operating_days": "Mon-Fri",
    },
]

_MOCK_PRICES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "market_id": 1,
        "market_name": "Ujjain APMC Mandi (Chimanganj Mandi)",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "arrival_date": date.today(),
        "min_price": 2420.0,
        "max_price": 2680.0,
        "modal_price": 2540.0,
        "arrivals_volume_tonnes": 1450.0,
        "latitude": 23.2014,
        "longitude": 75.7947,
    },
    {
        "id": 2,
        "market_id": 2,
        "market_name": "Indore Laxmi Bai Nagar APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "arrival_date": date.today(),
        "min_price": 2500.0,
        "max_price": 2750.0,
        "modal_price": 2640.0,
        "arrivals_volume_tonnes": 2100.0,
        "latitude": 22.7533,
        "longitude": 75.8637,
    },
    {
        "id": 3,
        "market_id": 3,
        "market_name": "Dewas APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Dewas",
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "arrival_date": date.today(),
        "min_price": 2390.0,
        "max_price": 2620.0,
        "modal_price": 2490.0,
        "arrivals_volume_tonnes": 820.0,
        "latitude": 22.9676,
        "longitude": 76.0534,
    },
    {
        "id": 4,
        "market_id": 4,
        "market_name": "Badnagar Sub-Mandi Yard",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "arrival_date": date.today(),
        "min_price": 2380.0,
        "max_price": 2550.0,
        "modal_price": 2460.0,
        "arrivals_volume_tonnes": 310.0,
        "latitude": 23.0634,
        "longitude": 75.3857,
    },
    {
        "id": 5,
        "market_id": 1,
        "market_name": "Ujjain APMC Mandi (Chimanganj Mandi)",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "variety": "JS-335",
        "arrival_date": date.today(),
        "min_price": 4250.0,
        "max_price": 4720.0,
        "modal_price": 4510.0,
        "arrivals_volume_tonnes": 1820.0,
        "latitude": 23.2014,
        "longitude": 75.7947,
    },
    {
        "id": 6,
        "market_id": 2,
        "market_name": "Indore Laxmi Bai Nagar APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "variety": "JS-335",
        "arrival_date": date.today(),
        "min_price": 4380.0,
        "max_price": 4890.0,
        "modal_price": 4650.0,
        "arrivals_volume_tonnes": 2900.0,
        "latitude": 22.7533,
        "longitude": 75.8637,
    },
]

_MOCK_MSP: List[Dict[str, Any]] = [
    {
        "id": 1,
        "commodity_id": 1,
        "commodity_name": "Wheat",
        "msp_price": 2275.0,  # Official GOI MSP 2024-25 / 2025-26
        "agency_name": "Food Corporation of India (FCI) / MP State Civil Supplies",
        "center_location": "Ujjain Central Rail-Head Silo, MP",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "latitude": 23.1950,
        "longitude": 75.8120,
        "active": True,
    },
    {
        "id": 2,
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "msp_price": 4892.0,  # GOI MSP for Soybean
        "agency_name": "NAFED State Procurement Center",
        "center_location": "Dewas Road Warehousing Complex, Indore, MP",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "latitude": 22.7680,
        "longitude": 75.8910,
        "active": True,
    },
]


# ==========================================
# Route Handlers
# ==========================================

@router.get("/prices", response_model=List[MarketPriceResponse], summary="Fetch Filtered Mandi Prices")
def get_market_prices(
    commodity_id: Optional[int] = Query(None, description="Filter by commodity ID"),
    commodity_name: Optional[str] = Query(None, description="Filter by commodity name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    mandi_id: Optional[int] = Query(None, description="Filter by specific mandi ID"),
    user_lat: Optional[float] = Query(None, description="Farmer latitude for distance & net realization estimation"),
    user_lng: Optional[float] = Query(None, description="Farmer longitude for distance & net realization estimation"),
    max_distance_km: Optional[float] = Query(None, description="Max road radius in km"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve live/recent APMC mandi prices and arrival volumes.
    Computes distance and estimated net realization if farmer location is provided.
    """
    results: List[MarketPriceResponse] = []

    for item in _MOCK_PRICES:
        if commodity_id and item["commodity_id"] != commodity_id:
            continue
        if commodity_name and commodity_name.lower() not in item["commodity_name"].lower():
            continue
        if state and state.lower() != item["state"].lower():
            continue
        if district and district.lower() != item["district"].lower():
            continue
        if mandi_id and item["market_id"] != mandi_id:
            continue

        dist: Optional[float] = None
        net_realization: Optional[float] = None

        if user_lat is not None and user_lng is not None and "latitude" in item:
            dist = calculate_road_distance_km(user_lat, user_lng, item["latitude"], item["longitude"])
            if max_distance_km and dist > max_distance_km:
                continue
            # Net Realization: Modal price minus estimated road freight (~₹2.50 per quintal per 10km)
            freight_deduction = max(25.0, round(dist * 0.45, 2))
            handling_cess = 15.0
            net_realization = round(item["modal_price"] - freight_deduction - handling_cess, 2)

        results.append(
            MarketPriceResponse(
                id=item["id"],
                market_id=item["market_id"],
                market_name=item["market_name"],
                state=item["state"],
                district=item["district"],
                commodity_id=item["commodity_id"],
                commodity_name=item["commodity_name"],
                variety=item["variety"],
                arrival_date=item["arrival_date"],
                min_price=item["min_price"],
                max_price=item["max_price"],
                modal_price=item["modal_price"],
                arrivals_volume_tonnes=item["arrivals_volume_tonnes"],
                distance_km=dist,
                estimated_net_realization_per_quintal=net_realization,
            )
        )

    return results


@router.get("/trends", response_model=MarketTrendsResponse, summary="Get Historical Price Trends & Arrival Volumes")
def get_price_trends(
    commodity_id: int = Query(1, description="Commodity ID"),
    market_id: int = Query(1, description="Mandi ID"),
    days_lookback: int = Query(30, ge=7, le=90, description="Historical window days"),
):
    """
    Generate date-indexed historical price and arrival volume series
    with 7-day and 30-day moving averages and trend direction.
    """
    today = date.today()
    series: List[PriceTrendPoint] = []

    # Baseline anchor price
    base_price = 2480.0 if commodity_id == 1 else 4450.0

    for i in range(days_lookback, 0, -1):
        cur_date = today - timedelta(days=i)
        # Gentle cyclical variation
        offset = math.sin(i / 4.0) * 45.0 + ((days_lookback - i) * 2.8)
        p = round(base_price + offset, 1)
        vol = round(800.0 + (math.cos(i / 3.0) * 250.0) + (i * 12.0), 1)
        series.append(
            PriceTrendPoint(
                date=cur_date,
                modal_price=p,
                min_price=round(p - 60.0, 1),
                max_price=round(p + 85.0, 1),
                arrivals_volume_tonnes=max(100.0, vol),
            )
        )

    # Today's point
    today_p = round(base_price + (days_lookback * 2.8), 1)
    series.append(
        PriceTrendPoint(
            date=today,
            modal_price=today_p,
            min_price=round(today_p - 70.0, 1),
            max_price=round(today_p + 90.0, 1),
            arrivals_volume_tonnes=1450.0,
        )
    )

    prices = [pt.modal_price for pt in series]
    p_7d = sum(prices[-7:]) / 7.0
    p_30d = sum(prices) / len(prices)
    price_change_pct = round(((prices[-1] - prices[0]) / prices[0]) * 100.0, 2)

    trend = PriceTrend.UPWARD if price_change_pct > 1.5 else (
        PriceTrend.DOWNWARD if price_change_pct < -1.5 else PriceTrend.STABLE
    )

    mandi_name = "Ujjain APMC Mandi"
    for m in _MOCK_MANDIS:
        if m["id"] == market_id:
            mandi_name = m["market_name"]
            break

    return MarketTrendsResponse(
        commodity_id=commodity_id,
        commodity_name="Wheat (Sharbati)" if commodity_id == 1 else "Soybean",
        market_id=market_id,
        market_name=mandi_name,
        series=series,
        average_price_7d=round(p_7d, 2),
        average_price_30d=round(p_30d, 2),
        trend=trend,
        price_change_pct=price_change_pct,
        volatility_score=3.2,
    )


@router.get("/mandis", response_model=List[MandiResponse], summary="Discover Registered Mandis")
def list_mandis(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    user_lat: Optional[float] = Query(None),
    user_lng: Optional[float] = Query(None),
):
    """Browse registered APMC Mandis with optional proximity calculation."""
    res = []
    for m in _MOCK_MANDIS:
        if state and state.lower() != m["state"].lower():
            continue
        if district and district.lower() != m["district"].lower():
            continue
        dist = None
        if user_lat is not None and user_lng is not None:
            dist = calculate_road_distance_km(user_lat, user_lng, m["latitude"], m["longitude"])
        res.append(MandiResponse(**m, distance_km=dist))
    return res


@router.post("/mandis", response_model=MandiResponse, status_code=status.HTTP_201_CREATED, summary="Register Mandi")
def create_mandi(payload: MandiCreate, db: Optional[Session] = Depends(get_db)):
    """Admin registration of a new regulated APMC Mandi."""
    new_id = max([m["id"] for m in _MOCK_MANDIS], default=0) + 1
    new_mandi = {"id": new_id, **payload.model_dump()}
    _MOCK_MANDIS.append(new_mandi)
    return MandiResponse(**new_mandi)


@router.get("/procurement-options", response_model=List[ProcurementOptionResponse], summary="List MSP Procurement Centers")
def list_procurement_options(
    commodity_id: Optional[int] = Query(None),
    user_lat: Optional[float] = Query(None),
    user_lng: Optional[float] = Query(None),
):
    """Query government MSP procurement centers (FCI, NAFED, state warehouses)."""
    res = []
    for opt in _MOCK_MSP:
        if commodity_id and opt["commodity_id"] != commodity_id:
            continue
        dist = None
        if user_lat is not None and user_lng is not None and opt.get("latitude") and opt.get("longitude"):
            dist = calculate_road_distance_km(user_lat, user_lng, opt["latitude"], opt["longitude"])
        res.append(ProcurementOptionResponse(**opt, distance_km=dist))
    return res


@router.post("/prices", response_model=MarketPriceResponse, status_code=status.HTTP_201_CREATED, summary="Ingest Price Record")
def ingest_price(payload: MarketPriceCreate):
    """Ingest daily mandi price record (from Agmarknet / e-NAM data feed)."""
    new_id = max([p["id"] for p in _MOCK_PRICES], default=0) + 1
    rec = {
        "id": new_id,
        "market_id": payload.market_id,
        "market_name": "APMC Mandi",
        "state": "Madhya Pradesh",
        "district": "Ujjain",
        "commodity_id": payload.commodity_id,
        "commodity_name": "Commodity",
        "variety": payload.variety,
        "arrival_date": payload.arrival_date,
        "min_price": payload.min_price,
        "max_price": payload.max_price,
        "modal_price": payload.modal_price,
        "arrivals_volume_tonnes": payload.arrivals_volume_tonnes,
    }
    _MOCK_PRICES.append(rec)
    return MarketPriceResponse(**rec)
