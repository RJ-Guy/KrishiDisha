"""
Decision Engine and Net Realization Optimization Router for KrishiDisha.
Translates agricultural commodity parameters, freight tariffs, storage costs,
and AI price forecasts into deterministic selling advice:
SELL NOW vs. WAIT vs. BEST BUYER.
Reinforces Government MSP awareness and comparative destination rankings.
"""

from datetime import date
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

# Schemas
from app.schemas.report_schema import (
    DecisionVerdict,
    SellingChannel,
    LiquidityUrgency,
    NetRealizationItem,
    MSPComparisonItem,
    DecisionRequest,
    DecisionRecommendationResponse,
)

# Helpers from other routes
from app.routes.market import calculate_road_distance_km
from app.routes.forecast import compute_forecast

router = APIRouter(prefix="/decision", tags=["Decision Analytics"])

# Official Government Minimum Support Prices (MSP) Reference
_GOI_MSP_BENCHMARKS = {
    1: {"commodity_name": "Wheat", "msp_price": 2275.0, "agency": "FCI / State Civil Supplies", "location": "Ujjain Central Silo, MP", "lat": 23.1950, "lng": 75.8120},
    2: {"commodity_name": "Soybean", "msp_price": 4892.0, "agency": "NAFED State Procurement Center", "location": "Dewas Road Hub, Indore, MP", "lat": 22.7680, "lng": 75.8910},
    3: {"commodity_name": "Gram (Chana)", "msp_price": 5440.0, "agency": "NAFED Mandi Procurement", "location": "Ujjain APMC Sub-Center, MP", "lat": 23.2014, "lng": 75.7947},
    4: {"commodity_name": "Mustard", "msp_price": 5650.0, "agency": "HAFED / NAFED Center", "location": "Malwa Regional Silo, MP", "lat": 22.9676, "lng": 76.0534},
}


@router.post("/recommend", response_model=DecisionRecommendationResponse, summary="Run Net Realization & Decision Engine")
def get_recommendation(payload: DecisionRequest):
    """
    Core Economic Optimization Engine:
    1. Computes Net Realization across multiple candidate selling channels:
       Net Realization = Gross Revenue - Transport - Storage - Handling - Taxes/Cess.
    2. Runs AI Price Forecast inference over user's holding horizon.
    3. Factors in daily storage holding tariffs and distress liquidity urgency.
    4. Benchmarks against official Government Minimum Support Price (MSP).
    5. Returns deterministic verdict: SELL NOW, WAIT, or BEST BUYER.
    """
    qty = payload.quantity_quintals
    horizon = payload.holding_horizon_days or 7
    daily_storage_rate = payload.storage_cost_per_quintal_day or 0.50

    # 1. Candidate Destinations
    candidates = [
        {
            "channel": SellingChannel.MANDI,
            "destination_name": "Ujjain APMC Mandi (Chimanganj Mandi)",
            "lat": 23.2014,
            "lng": 75.7947,
            "headline_price": 2540.0 if payload.commodity_id == 1 else 4510.0,
            "cess_pct": 0.015,  # 1.5% Mandi tax
            "handling_per_q": 12.0,
        },
        {
            "channel": SellingChannel.MANDI,
            "destination_name": "Indore Laxmi Bai Nagar APMC Mandi",
            "lat": 22.7533,
            "lng": 75.8637,
            "headline_price": 2640.0 if payload.commodity_id == 1 else 4650.0,
            "cess_pct": 0.015,
            "handling_per_q": 14.0,
        },
        {
            "channel": SellingChannel.INSTITUTIONAL_BUYER,
            "destination_name": "ITC Limited Agri Business (e-Choupal Hub)",
            "lat": 22.7712,
            "lng": 75.8941,
            "headline_price": 2680.0 if payload.commodity_id == 1 else 4750.0,
            "cess_pct": 0.0,  # Zero mandi cess for direct farmgate procurement
            "handling_per_q": 5.0,  # Direct mechanical unloading
        },
        {
            "channel": SellingChannel.MANDI,
            "destination_name": "Badnagar Sub-Mandi Yard",
            "lat": 23.0634,
            "lng": 75.3857,
            "headline_price": 2460.0 if payload.commodity_id == 1 else 4420.0,
            "cess_pct": 0.015,
            "handling_per_q": 10.0,
        },
    ]

    comparisons: List[NetRealizationItem] = []

    for cand in candidates:
        dist = calculate_road_distance_km(payload.origin_lat, payload.origin_lng, cand["lat"], cand["lng"])
        # Freight model: ₹14/km base + ₹0.40/Q/km
        freight_total = max(350.0, round((dist * 16.0) + (dist * qty * 0.38), 2))
        gross = round(cand["headline_price"] * qty, 2)
        handling = round(cand["handling_per_q"] * qty, 2)
        cess = round(gross * cand["cess_pct"], 2)
        storage_ded = 0.0  # Immediate sale has 0 storage

        net = round(gross - freight_total - handling - cess, 2)
        net_per_q = round(net / qty, 2)

        exp_note = (
            f"Headline ₹{cand['headline_price']:.0f}/Q minus freight (₹{freight_total / qty:.1f}/Q) "
            f"and handling/cess yields net ₹{net_per_q:.1f}/Q."
        )

        comparisons.append(
            NetRealizationItem(
                channel=cand["channel"],
                destination_name=cand["destination_name"],
                headline_price_per_quintal=cand["headline_price"],
                gross_revenue=gross,
                transport_cost=freight_total,
                storage_cost=storage_ded,
                handling_cost=handling,
                mandi_cess_and_taxes=cess,
                net_realization=net,
                net_price_per_quintal=net_per_q,
                distance_km=dist,
                explanation=exp_note,
            )
        )

    # Sort descending by Net Realization
    comparisons.sort(key=lambda x: x.net_realization, reverse=True)
    best_immediate = comparisons[0]

    # 2. AI Forecasting & Holding Simulation
    fc = compute_forecast(
        commodity_id=payload.commodity_id,
        market_id=1,
        horizon_days=horizon,
        current_price_override=best_immediate.headline_price_per_quintal,
    )
    price_delta = fc.expected_price_change
    total_holding_cost = round((daily_storage_rate * horizon * qty), 2)
    holding_cost_per_q = round(daily_storage_rate * horizon, 2)
    net_holding_gain_per_q = round(price_delta - holding_cost_per_q, 2)

    # 3. Decision Logic Formulation
    # If liquidity urgency is HIGH, farmer cannot wait regardless of gains
    if payload.liquidity_urgency == LiquidityUrgency.HIGH:
        verdict = DecisionVerdict.SELL_NOW
        headline = f"SELL NOW: Immediate cash requirement takes priority ({best_immediate.destination_name})"
        explanation = (
            f"Although future prices may fluctuate, your urgent liquidity priority indicates an immediate sale. "
            f"{best_immediate.destination_name} provides the highest immediate Net Realization of "
            f"₹{best_immediate.net_realization:,.0f} (₹{best_immediate.net_price_per_quintal:.1f}/Q)."
        )
    elif not payload.storage_available:
        verdict = DecisionVerdict.SELL_NOW
        headline = f"SELL NOW: Safe storage unavailable to withstand holding risks"
        explanation = (
            f"Without access to certified storage, spoilage and moisture degradation risks outweigh future price upside. "
            f"Selling immediately at {best_immediate.destination_name} guarantees ₹{best_immediate.net_realization:,.0f} net."
        )
    elif net_holding_gain_per_q > 45.0:  # Projected gain exceeds holding costs by healthy margin
        verdict = DecisionVerdict.WAIT
        future_net = round((best_immediate.net_price_per_quintal + net_holding_gain_per_q) * qty, 2)
        headline = f"WAIT: Hold produce for {horizon} days to capture expected ₹{net_holding_gain_per_q * qty:,.0f} net gain"
        explanation = (
            f"AI Forecast projects modal prices will rise by +₹{price_delta:.0f}/Q over {horizon} days. "
            f"After deducting storage holding costs of ₹{holding_cost_per_q:.1f}/Q, you are expected to gain an extra "
            f"+₹{net_holding_gain_per_q:.1f}/Q net (total extra ₹{net_holding_gain_per_q * qty:,.0f}). Store safely and re-evaluate."
        )
    elif best_immediate.channel == SellingChannel.INSTITUTIONAL_BUYER:
        verdict = DecisionVerdict.BEST_BUYER
        headline = f"BEST BUYER: Lock deal with {best_immediate.destination_name} for maximum net return"
        explanation = (
            f"Direct procurement by {best_immediate.destination_name} eliminates mandi cess and offers premium pricing, "
            f"yielding the top Net Realization of ₹{best_immediate.net_price_per_quintal:.1f}/Q. "
            f"This beats nearby open mandis by ₹{best_immediate.net_price_per_quintal - comparisons[1].net_price_per_quintal:.1f}/Q."
        )
    else:
        verdict = DecisionVerdict.SELL_NOW
        headline = f"SELL NOW: {best_immediate.destination_name} offers highest current net return"
        explanation = (
            f"Projected price gains (+₹{price_delta:.0f}/Q) are insufficient to offset storage costs and holding risks. "
            f"Selling immediately at {best_immediate.destination_name} locks in the best net price of "
            f"₹{best_immediate.net_price_per_quintal:.1f}/Q."
        )

    # 4. MSP Benchmark
    msp_item = None
    if payload.commodity_id in _GOI_MSP_BENCHMARKS:
        info = _GOI_MSP_BENCHMARKS[payload.commodity_id]
        msp_dist = calculate_road_distance_km(payload.origin_lat, payload.origin_lng, info["lat"], info["lng"])
        msp_freight = max(300.0, round((msp_dist * 16.0) + (msp_dist * qty * 0.38), 2))
        net_msp = round((info["msp_price"] * qty) - msp_freight, 2)
        premium = round(best_immediate.net_price_per_quintal - info["msp_price"], 2)
        msp_item = MSPComparisonItem(
            msp_price_per_quintal=info["msp_price"],
            agency_name=info["agency"],
            center_location=info["location"],
            distance_km=msp_dist,
            net_realization_msp=net_msp,
            is_above_msp=premium >= 0,
            premium_over_msp_per_quintal=premium,
        )

    return DecisionRecommendationResponse(
        verdict=verdict,
        headline_summary=headline,
        plain_text_explanation=explanation,
        best_channel=best_immediate.channel,
        best_destination_name=best_immediate.destination_name,
        expected_net_realization=best_immediate.net_realization,
        expected_net_price_per_quintal=best_immediate.net_price_per_quintal,
        channel_comparisons=comparisons,
        forecast_price_delta=price_delta,
        estimated_holding_cost=total_holding_cost,
        msp_benchmark=msp_item,
    )


@router.get("/msp-benchmark/{commodity_id}", response_model=MSPComparisonItem, summary="Get Government MSP Benchmark")
def get_msp_benchmark(
    commodity_id: int,
    user_lat: float = Query(23.4542, ge=-90.0, le=90.0),
    user_lng: float = Query(75.4168, ge=-180.0, le=180.0),
    quantity_quintals: float = Query(50.0, gt=0.0),
):
    """Compare current market price against official Government Minimum Support Price (MSP)."""
    if commodity_id not in _GOI_MSP_BENCHMARKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MSP data not available for commodity")

    info = _GOI_MSP_BENCHMARKS[commodity_id]
    dist = calculate_road_distance_km(user_lat, user_lng, info["lat"], info["lng"])
    freight = max(300.0, round((dist * 16.0) + (dist * quantity_quintals * 0.38), 2))
    net_msp = round((info["msp_price"] * quantity_quintals) - freight, 2)
    market_price = 2540.0 if commodity_id == 1 else 4510.0
    premium = round(market_price - info["msp_price"], 2)

    return MSPComparisonItem(
        msp_price_per_quintal=info["msp_price"],
        agency_name=info["agency"],
        center_location=info["location"],
        distance_km=dist,
        net_realization_msp=net_msp,
        is_above_msp=premium >= 0,
        premium_over_msp_per_quintal=premium,
    )
