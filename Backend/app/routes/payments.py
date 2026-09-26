"""
Payments, Escrow Management, and FPO Smallholder Payout Distribution
Router for KrishiDisha.
Supports secure escrow lock and release, digital transaction settlements,
and automated pro-rata smallholder payout breakdowns for aggregated bulk lots.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.payment_schema import (
    PaymentStatus,
    PaymentMethod,
    SmallholderPayout,
    PaymentCreate,
    PaymentStatusUpdate,
    EscrowStatusResponse,
    PaymentResponse,
)

# Dependencies
from app.routes.auth import get_db, get_current_user

# Access mock data from lots and offers
from app.routes.lots import _MOCK_AGGREGATIONS, _MOCK_LOTS
from app.routes.offers import _MOCK_TRANSACTIONS

router = APIRouter(prefix="/payments", tags=["Payments & Escrow"])

# ==========================================
# In-Memory Demonstration Store
# ==========================================
_MOCK_PAYMENTS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "transaction_id": 1,
        "amount": 169000.0,
        "payment_status": PaymentStatus.ESCROW_LOCKED,
        "payment_method": PaymentMethod.ESCROW,
        "reference_id": "ESCROW-TXN-2026-99214",
        "escrow_locked_at": datetime.now(timezone.utc),
        "released_at": None,
        "created_at": datetime.now(timezone.utc),
        "payout_breakdown": [
            {
                "farmer_id": 1,
                "farmer_name": "Ramesh Chandra Patel",
                "account_no_masked": "*******5678",
                "ifsc_code": "SBIN0001234",
                "quantity_contributed_quintals": 65.0,
                "share_pct": 100.0,
                "gross_payout": 169000.0,
                "pro_rata_deductions": 3250.0,
                "net_payout": 165750.0,
                "payout_status": PaymentStatus.ESCROW_LOCKED,
            }
        ],
    }
}


# ==========================================
# Route Handlers
# ==========================================

@router.get("", response_model=List[PaymentResponse], summary="List Payment Records")
def list_payments(current_user: Any = Depends(get_current_user)):
    """Retrieve payment and escrow records for authenticated user."""
    return [PaymentResponse(**p) for p in _MOCK_PAYMENTS.values()]


@router.get("/{payment_id}", response_model=PaymentResponse, summary="Get Payment Details by ID")
def get_payment(payment_id: int):
    """Retrieve full escrow breakdown and payout records for a payment."""
    if payment_id not in _MOCK_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")
    return PaymentResponse(**_MOCK_PAYMENTS[payment_id])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, summary="Initiate Escrow Deposit")
def create_payment(payload: PaymentCreate, current_user: Any = Depends(get_current_user)):
    """Initiate escrow deposit for an accepted transaction."""
    new_id = max(_MOCK_PAYMENTS.keys(), default=0) + 1
    new_pay = {
        "id": new_id,
        "transaction_id": payload.transaction_id,
        "amount": payload.amount,
        "payment_status": PaymentStatus.ESCROW_LOCKED,
        "payment_method": payload.payment_method,
        "reference_id": f"ESCROW-TXN-2026-{new_id:05d}",
        "escrow_locked_at": datetime.now(timezone.utc),
        "released_at": None,
        "created_at": datetime.now(timezone.utc),
        "payout_breakdown": [],
    }
    _MOCK_PAYMENTS[new_id] = new_pay
    return PaymentResponse(**new_pay)


@router.patch("/{payment_id}/status", response_model=PaymentResponse, summary="Update Payment Stage")
def update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    current_user: Any = Depends(get_current_user),
):
    """Update payment status (e.g., RELEASED upon delivery confirmation)."""
    if payment_id not in _MOCK_PAYMENTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    pay = _MOCK_PAYMENTS[payment_id]
    pay["payment_status"] = payload.new_status
    if payload.reference_id:
        pay["reference_id"] = payload.reference_id
    if payload.new_status == PaymentStatus.RELEASED:
        pay["released_at"] = datetime.now(timezone.utc)
        for pb in pay.get("payout_breakdown", []):
            pb["payout_status"] = PaymentStatus.RELEASED

    return PaymentResponse(**pay)


@router.get("/escrow/{transaction_id}", response_model=EscrowStatusResponse, summary="Inspect Escrow Status")
def get_escrow_status(transaction_id: int):
    """
    Inspect escrow security status:
    Verifies if funds are locked, whether delivery & inspection slip have been confirmed,
    and whether release conditions are met.
    """
    tx = _MOCK_TRANSACTIONS.get(transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    pay = next((p for p in _MOCK_PAYMENTS.values() if p["transaction_id"] == transaction_id), None)
    is_locked = pay is not None and pay["payment_status"] in (PaymentStatus.ESCROW_LOCKED, PaymentStatus.RELEASED)
    can_rel = tx["status"] in ("QUALITY_CONFIRMED", "SETTLED")

    return EscrowStatusResponse(
        transaction_id=transaction_id,
        escrow_amount=tx["gross_revenue"],
        is_locked=is_locked,
        locked_at=pay.get("escrow_locked_at") if pay else None,
        can_release=can_rel,
        message=(
            "Escrow funds locked securely. Ready for automated payout release."
            if can_rel else "Awaiting buyer quality inspection confirmation before escrow release."
        ),
    )


@router.post("/fpo-distribution/{bulk_lot_id}", response_model=List[SmallholderPayout], summary="Calculate Pro-Rata Smallholder Payouts")
def distribute_fpo_payouts(
    bulk_lot_id: int,
    total_net_realization: float = Query(..., gt=0.0, description="Total net payout received for the bulk lot"),
):
    """
    FPO Automated Payout Distribution Engine:
    Applies the sub-lot contribution shares from the bulk aggregation record
    to disburse transparent, itemized pro-rata bank payments to each contributing farmer.
    """
    if bulk_lot_id not in _MOCK_AGGREGATIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aggregated bulk lot contributions not found")

    contributions = _MOCK_AGGREGATIONS[bulk_lot_id]
    payouts: List[SmallholderPayout] = []

    for c in contributions:
        share = c["contribution_share_pct"] / 100.0
        gross_share = round(total_net_realization * share * 1.025, 2)  # Base gross
        deductions = round(gross_share - (total_net_realization * share), 2)
        net_share = round(total_net_realization * share, 2)

        payouts.append(
            SmallholderPayout(
                farmer_id=c["farmer_id"],
                farmer_name=c.get("farmer_name", "Smallholder Farmer"),
                account_no_masked=f"*******{c['farmer_id'] * 1234 % 9000 + 1000}",
                ifsc_code="SBIN0004567",
                quantity_contributed_quintals=c["quantity_quintals"],
                share_pct=c["contribution_share_pct"],
                gross_payout=gross_share,
                pro_rata_deductions=deductions,
                net_payout=net_share,
                payout_status=PaymentStatus.ESCROW_LOCKED,
            )
        )

    return payouts
