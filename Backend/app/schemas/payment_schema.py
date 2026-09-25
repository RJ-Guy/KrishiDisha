"""
Payment Tracking, Escrow Lifecycle, and Smallholder Payout Distribution
Pydantic Schemas for KrishiDisha.
Supports secure escrow lock/release, multi-farmer pro-rata disbursements,
and bank/UPI settlement logs.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    ESCROW_LOCKED = "ESCROW_LOCKED"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    NEFT_RTGS = "NEFT_RTGS"
    ESCROW = "ESCROW"
    DIRECT_BANK_TRANSFER = "DIRECT_BANK_TRANSFER"


# ==========================================
# Smallholder Pro-Rata Payout Schema
# ==========================================

class SmallholderPayout(BaseModel):
    farmer_id: int
    farmer_name: str
    account_no_masked: Optional[str] = Field(default=None, description="E.g., *******1234")
    ifsc_code: Optional[str] = None
    quantity_contributed_quintals: float = Field(..., gt=0.0)
    share_pct: float = Field(..., ge=0.0, le=100.0)
    gross_payout: float = Field(..., ge=0.0)
    pro_rata_deductions: float = Field(default=0.0, ge=0.0, description="Proportionate share of logistics & handling")
    net_payout: float = Field(..., ge=0.0, description="Gross payout - pro_rata_deductions")
    payout_status: PaymentStatus = PaymentStatus.PENDING


# ==========================================
# Escrow & Payment Lifecycle Schemas
# ==========================================

class PaymentCreate(BaseModel):
    transaction_id: int
    amount: float = Field(..., gt=0.0, description="Payment transaction amount in INR")
    payment_method: PaymentMethod = PaymentMethod.ESCROW
    payer_id: int
    payee_id: int
    notes: Optional[str] = None


class PaymentStatusUpdate(BaseModel):
    new_status: PaymentStatus
    reference_id: Optional[str] = Field(default=None, description="Bank UTR or gateway payment reference")
    remarks: Optional[str] = None


class EscrowStatusResponse(BaseModel):
    transaction_id: int
    escrow_amount: float
    is_locked: bool
    locked_at: Optional[datetime] = None
    can_release: bool = Field(..., description="True if delivery and inspection slip are fully accepted")
    message: str


class PaymentResponse(BaseModel):
    id: int
    transaction_id: int
    amount: float
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    reference_id: Optional[str] = None
    escrow_locked_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    created_at: datetime
    payout_breakdown: List[SmallholderPayout] = Field(
        default_factory=list,
        description="Itemized disbursements for pooled/aggregated smallholder lots"
    )

    model_config = ConfigDict(from_attributes=True)
