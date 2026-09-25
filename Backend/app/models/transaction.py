"""
SQLAlchemy ORM Models for Negotiation Offers, Deal Transactions,
Logistics Fleet Dispatch, and Escrow Payments.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.lot import Lot
    from app.models.buyer import Buyer, BuyerRequirement
    from app.models.user import User
    from app.models.grievance import Grievance


class Offer(Base):
    """
    Digital negotiation offers and counter-offers made on a Lot or Buyer Tender.
    """
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    requirement_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("buyer_requirements.id", ondelete="SET NULL"), nullable=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("buyers.id", ondelete="RESTRICT"), nullable=False)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    offered_price_per_quintal: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_quintals: Mapped[float] = mapped_column(Float, nullable=False)
    counter_price_per_quintal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True, nullable=False)
    last_acted_by: Mapped[str] = mapped_column(String(20), default="BUYER", nullable=False)
    delivery_terms: Mapped[Optional[str]] = mapped_column(String(50), default="EX_FARM", nullable=True)
    proposed_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    lot: Mapped[Optional["Lot"]] = relationship("Lot", back_populates="offers")
    requirement: Mapped[Optional["BuyerRequirement"]] = relationship("BuyerRequirement", back_populates="offers")
    buyer: Mapped["Buyer"] = relationship("Buyer", back_populates="offers")
    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction", back_populates="offer", uselist=False)


class Transaction(Base):
    """
    Binding contract locked upon offer acceptance.
    Maintains complete state machine lifecycle and Net Realization financials.
    """
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(Integer, ForeignKey("offers.id", ondelete="RESTRICT"), unique=True, nullable=False)
    agreed_price_per_quintal: Mapped[float] = mapped_column(Float, nullable=False)
    agreed_quantity_quintals: Mapped[float] = mapped_column(Float, nullable=False)
    gross_revenue: Mapped[float] = mapped_column(Float, nullable=False)  # Agreed Price * Agreed Quantity
    transport_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    storage_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    handling_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_realization: Mapped[float] = mapped_column(Float, nullable=False)  # Gross - Transport - Storage - Handling
    status: Mapped[str] = mapped_column(String(30), default="ACCEPTED", index=True, nullable=False)
    inspection_slip: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    offer: Mapped["Offer"] = relationship("Offer", back_populates="transaction")
    logistics: Mapped[Optional["Logistics"]] = relationship("Logistics", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="transaction", cascade="all, delete-orphan")
    grievances: Mapped[List["Grievance"]] = relationship("Grievance", back_populates="transaction")


class Logistics(Base):
    """
    Vehicle routing, freight tariff tracking, and dispatch state for a transaction.
    """
    __tablename__ = "logistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(30), nullable=False)  # MINI_TRUCK_1_5T, MEDIUM_TRUCK_5T, HEAVY_TRUCK_16T
    origin_address: Mapped[str] = mapped_column(String(250), nullable=False)
    destination_address: Mapped[str] = mapped_column(String(250), nullable=False)
    origin_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    destination_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    destination_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    driver_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)
    scheduled_pickup_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="logistics")


class Payment(Base):
    """
    Payment and escrow lifecycle for transactions, including smallholder disbursements.
    """
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), default="ESCROW", nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    payee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    escrow_locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payout_breakdown: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="payments")
    payer: Mapped["User"] = relationship("User", foreign_keys=[payer_id])
    payee: Mapped["User"] = relationship("User", foreign_keys=[payee_id])
