"""
SQLAlchemy ORM Models for Grievances, Disputes, and Resolution Audit Logs.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class Grievance(Base):
    """
    Transaction dispute logging for quality differences, weight discrepancies,
    transit damages, or payment withholding.
    """
    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    raised_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # QUALITY_DISPUTE, WEIGHT_DISCREPANCY, PAYMENT_DELAY, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    claimed_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True, nullable=False)  # OPEN, UNDER_REVIEW, RESOLVED, REJECTED, CLOSED
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    penalty_applied_to_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="grievances")
    raised_by_user: Mapped["User"] = relationship("User", foreign_keys=[raised_by_user_id], back_populates="grievances")
