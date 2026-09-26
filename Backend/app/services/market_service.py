"""
Market Intelligence and Mandi Price Analytics Service for KrishiDisha.
Processes live APMC mandi feeds, calculates rolling moving averages (7d, 30d),
detects directional price momentum, and generates distance-adjusted mandi rankings.
"""

import math
from datetime import date
from typing import Optional, List, Dict, Any, Tuple
from app.schemas.market_schema import (
    PriceTrend,
    PriceTrendPoint,
    MarketTrendsResponse,
    MarketPriceResponse,
)
from app.services.logistics_service import calculate_haversine_road_distance


def compute_price_series_analytics(
    commodity_id: int,
    commodity_name: str,
    market_id: int,
    market_name: str,
    series: List[PriceTrendPoint],
) -> MarketTrendsResponse:
    """
    Computes rolling price moving averages, percentage momentum,
    volatility dispersion, and trend classification (UPWARD, DOWNWARD, STABLE).
    """
    if not series:
        raise ValueError("Price series must not be empty.")

    prices = [p.modal_price for p in series]
    p_7d = sum(prices[-7:]) / len(prices[-7:]) if len(prices) >= 7 else sum(prices) / len(prices)
    p_30d = sum(prices) / len(prices)

    start_price = prices[0]
    end_price = prices[-1]
    pct_change = round(((end_price - start_price) / start_price) * 100.0, 2) if start_price else 0.0

    # Volatility: Standard deviation / Mean * 100
    mean_p = p_30d
    variance = sum((p - mean_p) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)
    volatility = round((std_dev / mean_p) * 100.0, 2) if mean_p else 0.0

    # Trend direction threshold: ±1.5%
    if pct_change > 1.5:
        trend = PriceTrend.UPWARD
    elif pct_change < -1.5:
        trend = PriceTrend.DOWNWARD
    else:
        trend = PriceTrend.STABLE

    return MarketTrendsResponse(
        commodity_id=commodity_id,
        commodity_name=commodity_name,
        market_id=market_id,
        market_name=market_name,
        series=series,
        average_price_7d=round(p_7d, 2),
        average_price_30d=round(p_30d, 2),
        trend=trend,
        price_change_pct=pct_change,
        volatility_score=volatility,
    )


def rank_mandis_by_net_realization(
    mandi_records: List[Dict[str, Any]],
    origin_lat: float,
    origin_lng: float,
    quantity_quintals: float = 50.0,
    max_distance_km: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates competing mandis:
    Calculates road distance, estimated freight deduction, and statutory mandi cess,
    ranking mandis strictly by Net Realization per Quintal.
    """
    results: List[Dict[str, Any]] = []

    for m in mandi_records:
        dest_lat = m.get("latitude") or m.get("lat") or 0.0
        dest_lng = m.get("longitude") or m.get("lng") or 0.0

        dist = calculate_haversine_road_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        if max_distance_km and dist > max_distance_km:
            continue

        modal_price = float(m["modal_price"])
        # Freight model: ₹14/km base + ₹0.38 per quintal per km
        freight_total = max(350.0, round((dist * 16.0) + (dist * quantity_quintals * 0.38), 2))
        freight_per_q = round(freight_total / quantity_quintals, 2)
        handling_per_q = 12.0
        cess_per_q = round(modal_price * 0.015, 2)  # 1.5% APMC tax

        net_price_per_q = round(modal_price - freight_per_q - handling_per_q - cess_per_q, 2)
        total_net = round(net_price_per_q * quantity_quintals, 2)

        results.append({
            "market_id": m.get("market_id", m.get("id")),
            "market_name": m["market_name"],
            "state": m.get("state", "Madhya Pradesh"),
            "district": m.get("district", "Ujjain"),
            "distance_km": dist,
            "headline_modal_price": modal_price,
            "freight_per_quintal": freight_per_q,
            "net_price_per_quintal": net_price_per_q,
            "total_net_realization": total_net,
            "advantage_vs_nearest": 0.0,  # Computed below
        })

    # Sort descending by net price per quintal
    results.sort(key=lambda x: x["net_price_per_quintal"], reverse=True)

    # Compute advantage vs closest mandi
    if results:
        closest = min(results, key=lambda x: x["distance_km"])
        for r in results:
            r["advantage_vs_nearest"] = round(r["net_price_per_quintal"] - closest["net_price_per_quintal"], 2)

    return results
