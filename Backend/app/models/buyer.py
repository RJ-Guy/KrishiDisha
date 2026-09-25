"""
SQLAlchemy ORM Models for Buyers and Reverse Marketplace Requirements/Tenders.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.market import Commodity
    from app.models.transaction import Offer


class Buyer(Base):
    """
    Verified institutional buyers, food processors, exporters, and private traders.
    """
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gst_no: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    trade_license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    buyer_category: Mapped[str] = mapped_column(String(50), default="INSTITUTIONAL", nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operating_states: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    on_time_payment_rate_pct: Mapped[float] = mapped_column(Float, default=95.0, nullable=False)
    total_deals_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="buyer_profile")
    requirements: Mapped[List["BuyerRequirement"]] = relationship("BuyerRequirement", back_populates="buyer", cascade="all, delete-orphan")


class BuyerRequirement(Base):
    """
    Reverse marketplace procurement tenders posted by institutional buyers.
    E.g., "Wheat, Grade A, Moisture <= 12%, 500 Quintals".
    """
    __tablename__ = "buyer_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("buyers.id", ondelete="CASCADE"), nullable=False)
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("commodities.id", ondelete="RESTRICT"), nullable=False)
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    required_quantity_quintals: Mapped[float] = mapped_column(Float, nullable=False)
    max_price_per_quintal: Mapped[float] = mapped_column(Float, nullable=False)
    min_grade: Mapped[str] = mapped_column(String(20), default="GRADE_A", nullable=False)
    max_moisture_pct: Mapped[float] = mapped_column(Float, default=12.0, nullable=False)
    delivery_location_name: Mapped[str] = mapped_column(String(200), nullable=False)
    delivery_location_lat: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_location_lng: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_window_start: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_window_end: Mapped[date] = mapped_column(Date, nullable=False)
    special_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True, nullable=False)
    fulfilled_quantity_quintals: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="requirements")
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="buyer_requirements")
    offers: Mapped[List["Offer"]] = relationship("Offer", back_populates="requirement")
