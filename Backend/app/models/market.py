"""
SQLAlchemy ORM Models for Commodities, Mandis, Market Prices, Storage Facilities,
MSP Procurement Centers, and ML Forecasts.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.lot import Lot
    from app.models.buyer import BuyerRequirement


class Commodity(Base):
    """
    Standard agricultural commodities tracked by KrishiDisha.
    E.g. Wheat, Soybean, Mustard, Cotton, Chana.
    """
    __tablename__ = "commodities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Cereal, Pulse, Oilseed, etc.
    standard_unit: Mapped[str] = mapped_column(String(20), default="Quintal", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    market_prices: Mapped[List["MarketPrice"]] = relationship("MarketPrice", back_populates="commodity")
    lots: Mapped[List["Lot"]] = relationship("Lot", back_populates="commodity")
    buyer_requirements: Mapped[List["BuyerRequirement"]] = relationship("BuyerRequirement", back_populates="commodity")
    forecasts: Mapped[List["Forecast"]] = relationship("Forecast", back_populates="commodity")
    procurement_options: Mapped[List["ProcurementOption"]] = relationship("ProcurementOption", back_populates="commodity")


class Market(Base):
    """
    Physical APMC Mandis and regulated agricultural trading hubs.
    """
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_apmc: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    operating_days: Mapped[Optional[str]] = mapped_column(String(100), default="Mon-Sat", nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    market_prices: Mapped[List["MarketPrice"]] = relationship("MarketPrice", back_populates="market")
    forecasts: Mapped[List["Forecast"]] = relationship("Forecast", back_populates="market")


class MarketPrice(Base):
    """
    Daily arrival and modal price records scraped or synced from e-NAM / Agmarknet / data.gov.in.
    """
    __tablename__ = "market_prices"
    __table_args__ = (
        Index("idx_mkt_price_lookup", "commodity_id", "market_id", "arrival_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    arrivals_volume_tonnes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="market_prices")
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="market_prices")


class ProcurementOption(Base):
    """
    Government Minimum Support Price (MSP) centers (FCI, NAFED, state agencies).
    """
    __tablename__ = "procurement_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    msp_price: Mapped[float] = mapped_column(Float, nullable=False)
    agency_name: Mapped[str] = mapped_column(String(150), nullable=False)
    center_location: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="procurement_options")


class StorageOption(Base):
    """
    Agricultural warehousing, cold storages, and WDRA accredited facilities.
    """
    __tablename__ = "storage_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    facility_name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    daily_cost_per_quintal: Mapped[float] = mapped_column(Float, default=0.50, nullable=False)
    capacity_quintals: Mapped[float] = mapped_column(Float, default=1000.0, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)


class Forecast(Base):
    """
    Temporal price forecasts generated by the LightGBM/Ridge regression ML models.
    """
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    market_id: Mapped[int] = mapped_column(Integer, ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    predicted_modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=False)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=False)
    trend: Mapped[str] = mapped_column(String(20), default="STABLE", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    trajectory_data: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0-lightgbm", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="forecasts")
    market: Mapped["Market"] = relationship("Market", back_populates="forecasts")
