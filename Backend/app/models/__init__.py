"""
KrishiDisha SQLAlchemy Models Registry.
Declares Base and exports all 17+ core relational models for Alembic migrations,
database seeding, and service layer queries.
"""

from typing import Any

# Shared Declarative Base
try:
    from app.database.connection import Base
except (ImportError, AttributeError):
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

# Import models to register them on Base.metadata
from app.models.user import User, Farmer, FPO
from app.models.buyer import Buyer, BuyerRequirement
from app.models.market import (
    Commodity,
    Market,
    MarketPrice,
    ProcurementOption,
    StorageOption,
    Forecast,
)
from app.models.lot import Lot, SubLotContribution
from app.models.transaction import Offer, Transaction, Logistics, Payment
from app.models.grievance import Grievance

__all__ = [
    "Base",
    "User",
    "Farmer",
    "FPO",
    "Buyer",
    "BuyerRequirement",
    "Commodity",
    "Market",
    "MarketPrice",
    "ProcurementOption",
    "StorageOption",
    "Forecast",
    "Lot",
    "SubLotContribution",
    "Offer",
    "Transaction",
    "Logistics",
    "Payment",
    "Grievance",
]
