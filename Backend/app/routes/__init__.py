"""
KrishiDisha Central API Router Registry.
Aggregates and mounts all 12 feature sub-routers under the `/api` prefix,
providing a unified, type-safe REST interface for the KrishiDisha platform.
"""

from fastapi import APIRouter

# Import Sub-Routers
from app.routes.auth import router as auth_router
from app.routes.lots import router as lots_router
from app.routes.market import router as market_router
from app.routes.forecast import router as forecast_router
from app.routes.buyers import router as buyers_router
from app.routes.offers import router as offers_router
from app.routes.transactions import router as transactions_router
from app.routes.logistics import router as logistics_router
from app.routes.decision import router as decision_router
from app.routes.payments import router as payments_router
from app.routes.grievances import router as grievances_router
from app.routes.reports import router as reports_router

# Master Router
api_router = APIRouter(prefix="/api")

# Register Feature Sub-Routers
api_router.include_router(auth_router)
api_router.include_router(lots_router)
api_router.include_router(market_router)
api_router.include_router(forecast_router)
api_router.include_router(buyers_router)
api_router.include_router(offers_router)
api_router.include_router(transactions_router)
api_router.include_router(logistics_router)
api_router.include_router(decision_router)
api_router.include_router(payments_router)
api_router.include_router(grievances_router)
api_router.include_router(reports_router)


@api_router.get("/health", tags=["System Health"], summary="KrishiDisha API Health Check")
def health_check():
    """Returns operational status and active engine components."""
    return {
        "status": "healthy",
        "service": "KrishiDisha API Engine",
        "version": "1.0.0",
        "sih_problem_statement": "26132",
        "active_modules": [
            "Authentication & RBAC",
            "Digital Lots & FPO Aggregation",
            "Market Intelligence & Mandi Prices",
            "AI Price Forecasting (LightGBM/Ridge)",
            "Buyer Discovery & Reverse Tenders",
            "Multi-Factor Buyer Matching Engine",
            "Digital Negotiations & Offers",
            "Transaction State Machine",
            "Logistics & OSRM Tariff Engine",
            "Net Realization Decision Engine (SELL/WAIT/BEST BUYER)",
            "Escrow & Smallholder Pro-Rata Payouts",
            "Grievances & Trust Auditing",
            "Variance Analysis & Feedback Loop",
        ],
    }


# Standard alias
router = api_router

__all__ = [
    "api_router",
    "router",
    "auth_router",
    "lots_router",
    "market_router",
    "forecast_router",
    "buyers_router",
    "offers_router",
    "transactions_router",
    "logistics_router",
    "decision_router",
    "payments_router",
    "grievances_router",
    "reports_router",
]
