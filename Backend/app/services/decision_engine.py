"""
SELL NOW vs. WAIT vs. BEST BUYER Decision Engine for KrishiDisha.
Translates agricultural commodity parameters, freight tariffs, storage costs,
and AI price forecasts into deterministic selling advice.
Balancing price trajectory against holding costs and quality decay risks.
"""

from typing import Optional, List, Dict, Any
from app.schemas.report_schema import (
    DecisionVerdict,
    SellingChannel,
    LiquidityUrgency,
    NetRealizationItem,
    MSPComparisonItem,
    DecisionRequest,
    DecisionRecommendationResponse,
)
from app.services.net_realization import compare_destinations
from app.services.logistics_service import calculate_haversine_road_distance

# Official Government Minimum Support Prices (MSP) Reference
MSP_BENCHMARKS: Dict[int, Dict[str, Any]] = {
    1: {"name": "Wheat", "msp_price": 2275.0, "agency": "Food Corporation of India (FCI)", "location": "Ujjain Central Silo, MP", "lat": 23.1950, "lng": 75.8120},
    2: {"name": "Soybean (Yellow)", "msp_price": 4892.0, "agency": "NAFED State Procurement Center", "location": "Dewas Road Hub, Indore, MP", "lat": 22.7680, "lng": 75.8910},
    3: {"name": "Gram (Chana)", "msp_price": 5440.0, "agency": "NAFED Mandi Procurement", "location": "Ujjain APMC Sub-Center, MP", "lat": 23.2014, "lng": 75.7947},
    4: {"name": "Mustard", "msp_price": 5650.0, "agency": "HAFED / NAFED Center", "location": "Malwa Regional Silo, MP", "lat": 22.9676, "lng": 76.0534},
}

# Standard Default Candidate Destinations (Malwa Agritech Cluster, MP)
DEFAULT_DESTINATIONS: List[Dict[str, Any]] = [
    {
        "channel": SellingChannel.MANDI,
        "destination_name": "Ujjain APMC Mandi (Chimanganj Mandi)",
        "lat": 23.2014,
        "lng": 75.7947,
        "headline_price": 2540.0,
        "cess_pct": 0.015,
        "handling_per_q": 12.0,
    },
    {
        "channel": SellingChannel.MANDI,
        "destination_name": "Indore Laxmi Bai Nagar APMC Mandi",
        "lat": 22.7533,
        "lng": 75.8637,
        "headline_price": 2640.0,
        "cess_pct": 0.015,
        "handling_per_q": 14.0,
    },
    {
        "channel": SellingChannel.INSTITUTIONAL_BUYER,
        "destination_name": "ITC Limited Agri Business (e-Choupal Hub)",
        "lat": 22.7712,
        "lng": 75.8941,
        "headline_price": 2680.0,
        "cess_pct": 0.0,  # Zero mandi cess for direct farmgate procurement
        "handling_per_q": 5.0,  # Mechanical bulk unloading
    },
    {
        "channel": SellingChannel.MANDI,
        "destination_name": "Badnagar Sub-Mandi Yard",
        "lat": 23.0634,
        "lng": 75.3857,
        "headline_price": 2460.0,
        "cess_pct": 0.015,
        "handling_per_q": 10.0,
    },
]


def evaluate_selling_decision(
    commodity_id: int,
    quantity_quintals: float,
    origin_lat: float,
    origin_lng: float,
    variety: str = "Standard",
    quality_grade: str = "GRADE_A",
    moisture_pct: float = 11.5,
    storage_available: bool = True,
    storage_cost_per_quintal_day: float = 0.50,
    liquidity_urgency: LiquidityUrgency = LiquidityUrgency.MEDIUM,
    holding_horizon_days: int = 7,
    candidate_destinations: Optional[List[Dict[str, Any]]] = None,
    forecast_price_delta: Optional[float] = None,
) -> DecisionRecommendationResponse:
    """
    Core Economic Decision Engine:
    Evaluates multi-destination Net Realizations, holding costs, price forecast delta,
    and cash urgency to produce a deterministic, explainable selling verdict.
    """
    if quantity_quintals <= 0:
        raise ValueError("Quantity must be greater than zero")

    dests = candidate_destinations or DEFAULT_DESTINATIONS

    # Adjust default prices for soybean vs wheat
    if candidate_destinations is None and commodity_id == 2:
        dests = [
            {**d, "headline_price": d["headline_price"] + 1950.0}
            for d in DEFAULT_DESTINATIONS
        ]

    # 1. Multi-Destination Net Realization Comparison
    ranked_options = compare_destinations(
        destinations=dests,
        quantity_quintals=quantity_quintals,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        storage_cost=0.0,
    )
    best_immediate = ranked_options[0]

    # 2. Forecasting & Holding Cost Evaluation
    # Default forecast delta heuristic if not injected: +₹18.5/Q per day for wheat, -₹12/Q for soybean
    if forecast_price_delta is None:
        daily_drift = 18.5 if commodity_id == 1 else -12.0
        predicted_delta = round(daily_drift * holding_horizon_days * 0.95, 1)
    else:
        predicted_delta = round(forecast_price_delta, 1)

    total_holding_cost = round(storage_cost_per_quintal_day * holding_horizon_days * quantity_quintals, 2)
    holding_cost_per_q = round(storage_cost_per_quintal_day * holding_horizon_days, 2)

    # Risk penalty discount (perishability and confidence haircut)
    risk_haircut_per_q = 5.0
    net_holding_benefit_per_q = round(predicted_delta - holding_cost_per_q - risk_haircut_per_q, 2)

    # 3. Decision Logic Formulation
    if liquidity_urgency == LiquidityUrgency.HIGH:
        verdict = DecisionVerdict.SELL_NOW
        headline = f"SELL NOW: Immediate cash liquidity takes priority ({best_immediate.destination_name})"
        explanation = (
            f"Your high urgency for immediate liquidity indicates selling now rather than waiting. "
            f"{best_immediate.destination_name} provides the highest current Net Realization of "
            f"₹{best_immediate.net_realization:,.0f} (₹{best_immediate.net_price_per_quintal:,.1f}/Q)."
        )
    elif not storage_available:
        verdict = DecisionVerdict.SELL_NOW
        headline = "SELL NOW: Safe warehousing unavailable; sell immediately to prevent decay"
        explanation = (
            f"Without certified storage access, moisture absorption and pest spoilage risks erode potential price gains. "
            f"Selling immediately at {best_immediate.destination_name} guarantees ₹{best_immediate.net_realization:,.0f} net."
        )
    elif net_holding_benefit_per_q > 35.0:  # Favorable net surge after storage
        verdict = DecisionVerdict.WAIT
        extra_net = round(net_holding_benefit_per_q * quantity_quintals, 2)
        headline = f"WAIT: Hold produce for {holding_horizon_days} days to capture estimated +₹{extra_net:,.0f} net gain"
        explanation = (
            f"AI Price Forecast projects prices will rise by +₹{predicted_delta:,.0f}/Q over {holding_horizon_days} days. "
            f"After deducting storage costs of ₹{holding_cost_per_q:,.1f}/Q, you gain an extra "
            f"+₹{net_holding_benefit_per_q:,.1f}/Q net (total extra ₹{extra_net:,.0f}). Store produce safely in warehouse."
        )
    elif best_immediate.channel == SellingChannel.INSTITUTIONAL_BUYER:
        verdict = DecisionVerdict.BEST_BUYER
        headline = f"BEST BUYER: Lock direct deal with {best_immediate.destination_name}"
        margin_over_second = round(best_immediate.net_price_per_quintal - ranked_options[1].net_price_per_quintal, 2)
        explanation = (
            f"Direct procurement by {best_immediate.destination_name} eliminates statutory mandi cess and offers premium pricing, "
            f"yielding the highest Net Realization of ₹{best_immediate.net_price_per_quintal:,.1f}/Q "
            f"(+₹{margin_over_second:,.1f}/Q higher than nearest open APMC mandi)."
        )
    else:
        verdict = DecisionVerdict.SELL_NOW
        headline = f"SELL NOW: {best_immediate.destination_name} offers highest current net in-pocket return"
        explanation = (
            f"Future price increase (+₹{predicted_delta:,.0f}/Q) is insufficient to compensate for storage fees and holding risk. "
            f"Selling now at {best_immediate.destination_name} secures ₹{best_immediate.net_price_per_quintal:,.1f}/Q net."
        )

    # 4. MSP Benchmark
    msp_item = None
    if commodity_id in MSP_BENCHMARKS:
        info = MSP_BENCHMARKS[commodity_id]
        msp_dist = calculate_haversine_road_distance(origin_lat, origin_lng, info["lat"], info["lng"])
        msp_freight = max(300.0, round((msp_dist * 16.0) + (msp_dist * quantity_quintals * 0.38), 2))
        net_msp = round((info["msp_price"] * quantity_quintals) - msp_freight, 2)
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
        channel_comparisons=ranked_options,
        forecast_price_delta=predicted_delta,
        estimated_holding_cost=total_holding_cost,
        msp_benchmark=msp_item,
    )
