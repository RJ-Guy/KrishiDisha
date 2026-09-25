"""
KrishiDisha Core Services & Quantitative Business Logic Registry.
Exports all economic calculation engines, decision models, matching heuristics,
and logistics estimators for seamless import across route handlers, pipelines, and tests.
"""

from app.services.net_realization import (
    calculate_net_realization,
    compare_destinations,
    calculate_realization_variance,
)

from app.services.decision_engine import (
    evaluate_selling_decision,
    MSP_BENCHMARKS,
)

from app.services.buyer_matching import (
    match_lot_to_buyers,
    DEFAULT_BUYER_REQUIREMENTS,
)

from app.services.bulk_aggregation import (
    validate_child_lots,
    aggregate_smallholder_lots,
    compute_smallholder_payouts,
)

from app.services.logistics_service import (
    calculate_haversine_road_distance,
    select_vehicle_fleet,
    compute_freight_quote,
    VEHICLE_CONFIGS,
)

from app.services.market_service import (
    compute_price_series_analytics,
    rank_mandis_by_net_realization,
)

__all__ = [
    # Net Realization Engine
    "calculate_net_realization",
    "compare_destinations",
    "calculate_realization_variance",
    # Decision Engine
    "evaluate_selling_decision",
    "MSP_BENCHMARKS",
    # Buyer Matching Engine
    "match_lot_to_buyers",
    "DEFAULT_BUYER_REQUIREMENTS",
    # Bulk Aggregation Engine
    "validate_child_lots",
    "aggregate_smallholder_lots",
    "compute_smallholder_payouts",
    # Logistics Engine
    "calculate_haversine_road_distance",
    "select_vehicle_fleet",
    "compute_freight_quote",
    "VEHICLE_CONFIGS",
    # Market Intelligence Service
    "compute_price_series_analytics",
    "rank_mandis_by_net_realization",
]
