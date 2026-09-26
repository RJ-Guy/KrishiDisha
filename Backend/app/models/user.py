"""
SQLAlchemy ORM Models for User Accounts, Farmers, and FPOs in KrishiDisha.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.buyer import Buyer
    from app.models.lot import Lot
    from app.models.grievance import Grievance


class User(Base):
    """
    Core authentication and identity entity.
    Roles: FARMER, FPO, BUYER, ADMIN.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="FARMER", nullable=False)
    language_preference: Mapped[str] = mapped_column(String(10), default="hi", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # 1-to-1 Profile Relationships
    farmer_profile: Mapped[Optional["Farmer"]] = relationship("Farmer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    fpo_profile: Mapped[Optional["FPO"]] = relationship("FPO", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile: Mapped[Optional["Buyer"]] = relationship("Buyer", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # 1-to-Many Relationships
    grievances: Mapped[List["Grievance"]] = relationship("Grievance", foreign_keys="[Grievance.raised_by_user_id]", back_populates="raised_by_user")


class Farmer(Base):
    """
    Farmer demographic and landholding details.
    """
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    village: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    land_size_acres: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_crops: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    fpo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("fpos.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="farmer_profile")
    fpo: Mapped[Optional["FPO"]] = relationship("FPO", back_populates="member_farmers")


class FPO(Base):
    """
    Farmer Producer Organization entity coordinating member farmers and bulk aggregation.
    """
    __tablename__ = "fpos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_capacity_quintals: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="fpo_profile")
    member_farmers: Mapped[List["Farmer"]] = relationship("Farmer", back_populates="fpo")
