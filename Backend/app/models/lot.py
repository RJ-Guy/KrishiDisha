"""
SQLAlchemy ORM Models for Commodity Lots, Quality Parameters,
and FPO Bulk Aggregation with Complete Origin Traceability.
"""

from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.market import Commodity
    from app.models.user import Farmer
    from app.models.transaction import Offer


class Lot(Base):
    """
    Digital lot created by a Farmer or FPO.
    Supports individual lots and master aggregated bulk lots.
    """
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_type: Mapped[str] = mapped_column(String(20), default="FARMER", nullable=False)  # FARMER, FPO
    owner_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    parent_bulk_lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lots.id", ondelete="SET NULL"), nullable=True)
    commodity_id: Mapped[int] = mapped_column(Integer, ForeignKey("commodities.id", ondelete="RESTRICT"), nullable=False)
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity_quintals: Mapped[float] = mapped_column(Float, nullable=False)
    quality_grade: Mapped[str] = mapped_column(String(20), default="FAQ", nullable=False)  # GRADE_A, GRADE_B, FAQ
    moisture_pct: Mapped[float] = mapped_column(Float, nullable=False)
    storage_state: Mapped[str] = mapped_column(String(30), default="FARM_STORED", nullable=False)
    location_address: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    location_lat: Mapped[float] = mapped_column(Float, nullable=False)
    location_lng: Mapped[float] = mapped_column(Float, nullable=False)
    harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_selling_window_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_selling_window_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    minimum_acceptable_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="lots")

    # Self-referential tree for parent/child aggregation
    parent_bulk_lot: Mapped[Optional["Lot"]] = relationship("Lot", remote_side="[Lot.id]", back_populates="child_lots")
    child_lots: Mapped[List["Lot"]] = relationship("Lot", back_populates="parent_bulk_lot")

    # Explicit origin traceability
    contributions_received: Mapped[List["SubLotContribution"]] = relationship(
        "SubLotContribution",
        foreign_keys="[SubLotContribution.master_bulk_lot_id]",
        back_populates="master_bulk_lot",
        cascade="all, delete-orphan",
    )
    contribution_made: Mapped[Optional["SubLotContribution"]] = relationship(
        "SubLotContribution",
        foreign_keys="[SubLotContribution.child_lot_id]",
        back_populates="child_lot",
        uselist=False,
    )

    offers: Mapped[List["Offer"]] = relationship("Offer", back_populates="lot")


class SubLotContribution(Base):
    """
    Preserves exact contribution records of individual smallholders
    contributing to an aggregated FPO bulk lot.
    """
    __tablename__ = "sub_lot_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    master_bulk_lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    child_lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), unique=True, nullable=False)
    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False)
    quantity_quintals: Mapped[float] = mapped_column(Float, nullable=False)
    moisture_pct: Mapped[float] = mapped_column(Float, nullable=False)
    quality_grade: Mapped[str] = mapped_column(String(20), nullable=False)
    contribution_share_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    master_bulk_lot: Mapped["Lot"] = relationship("Lot", foreign_keys=[master_bulk_lot_id], back_populates="contributions_received")
    child_lot: Mapped["Lot"] = relationship("Lot", foreign_keys=[child_lot_id], back_populates="contribution_made")
    farmer: Mapped["Farmer"] = relationship("Farmer")
