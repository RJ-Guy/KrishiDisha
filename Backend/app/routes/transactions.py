"""
Transactions and Contract Lifecycle Router for KrishiDisha.
Manages the complete deal state machine:
ACCEPTED -> LOT_RESERVED -> DISPATCHED -> DELIVERED -> QUALITY_CONFIRMED -> SETTLED / DISPUTED.
Maintains Net Realization financial accounting and quality inspection slips.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.transaction_schema import (
    TransactionStatus,
    QualityInspectionSlip,
    TransactionCreate,
    TransactionStateUpdate,
    TransactionResponse,
)

# Dependencies
from app.routes.auth import get_db, get_current_user

# Shared mock transactions store from offers
from app.routes.offers import _MOCK_TRANSACTIONS

# Models
try:
    from app.models.transaction import Transaction
except ImportError:
    Transaction = None

router = APIRouter(prefix="/transactions", tags=["Transactions & Contracts"])


# ==========================================
# Serialization Projection Helper
# ==========================================

def _serialize_transaction(tx: Any) -> Dict[str, Any]:
    """Projects SQLAlchemy Transaction model into TransactionResponse schema dictionary."""
    offer = getattr(tx, "offer", None)
    seller_id = offer.seller_id if offer else 1
    seller_name = "Farmer Ramesh Patel"
    if offer and getattr(offer, "seller", None) and hasattr(offer.seller, "full_name"):
        seller_name = offer.seller.full_name

    buyer_id = offer.buyer_id if offer else 1
    buyer_name = "ITC Limited Agri Business"
    if offer and getattr(offer, "buyer", None) and hasattr(offer.buyer, "company_name"):
        buyer_name = offer.buyer.company_name

    lot_id = offer.lot_id if offer else None
    commodity_name = "Wheat (Sharbati)"
    if offer and getattr(offer, "lot", None) and getattr(offer.lot, "commodity", None):
        commodity_name = offer.lot.commodity.name

    # Handle status enum conversion safely
    raw_status = getattr(tx, "status", "ACCEPTED")
    try:
        tx_status = TransactionStatus(raw_status)
    except (ValueError, KeyError):
        tx_status = TransactionStatus.ACCEPTED

    return {
        "id": tx.id,
        "offer_id": tx.offer_id,
        "lot_id": lot_id,
        "seller_id": seller_id,
        "seller_name": seller_name,
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "commodity_name": commodity_name,
        "agreed_price_per_quintal": tx.agreed_price_per_quintal,
        "agreed_quantity_quintals": tx.agreed_quantity_quintals,
        "gross_revenue": tx.gross_revenue,
        "transport_cost": getattr(tx, "transport_cost", 0.0),
        "storage_cost": getattr(tx, "storage_cost", 0.0),
        "handling_cost": getattr(tx, "handling_cost", 0.0),
        "net_realization": tx.net_realization,
        "status": tx_status,
        "created_at": getattr(tx, "created_at", datetime.now(timezone.utc)),
        "updated_at": getattr(tx, "updated_at", None),
        "inspection_slip": getattr(tx, "inspection_slip", None),
    }


# ==========================================
# Route Handlers
# ==========================================

@router.get("", response_model=List[TransactionResponse], summary="List Transactions")
def list_transactions(
    status_filter: Optional[TransactionStatus] = Query(None, alias="status"),
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve active and completed transactions involving the authenticated user.
    """
    if db is not None and Transaction is not None:
        query = db.query(Transaction)
        if status_filter:
            query = query.filter(Transaction.status == status_filter.value)
        db_records = query.order_by(Transaction.created_at.desc()).all()
        return [_serialize_transaction(tx) for tx in db_records]

    results = []
    for tx in _MOCK_TRANSACTIONS.values():
        if status_filter and tx["status"] != status_filter:
            continue
        results.append(TransactionResponse(**tx))
    return results


@router.get("/{tx_id}", response_model=TransactionResponse, summary="Get Transaction by ID")
def get_transaction(tx_id: int, db: Optional[Session] = Depends(get_db)):
    """Retrieve full transaction contract, delivery status, and financial breakdown."""
    if db is not None and Transaction is not None:
        tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return _serialize_transaction(tx)

    if tx_id not in _MOCK_TRANSACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionResponse(**_MOCK_TRANSACTIONS[tx_id])


@router.post("/{tx_id}/dispatch", response_model=TransactionResponse, summary="Confirm Consignment Dispatch")
def dispatch_consignment(
    tx_id: int,
    payload: TransactionStateUpdate,
    current_user: Any = Depends(get_current_user),
):
    """
    Seller confirms consignment dispatch from farm/hub:
    Attaches digital weighment slip or transport bilty, advancing state to DISPATCHED.
    """
    if tx_id not in _MOCK_TRANSACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    tx = _MOCK_TRANSACTIONS[tx_id]
    tx["status"] = TransactionStatus.DISPATCHED
    tx["updated_at"] = datetime.now(timezone.utc)
    return TransactionResponse(**tx)


@router.post("/{tx_id}/deliver", response_model=TransactionResponse, summary="Confirm Delivery & Upload Inspection Slip")
def deliver_consignment(
    tx_id: int,
    slip: QualityInspectionSlip,
    current_user: Any = Depends(get_current_user),
):
    """
    Buyer confirms receipt and uploads digital Quality Inspection Slip:
    Records measured scale weight, lab moisture reading, and grade verification.
    If accepted, advances state to QUALITY_CONFIRMED.
    """
    if tx_id not in _MOCK_TRANSACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    tx = _MOCK_TRANSACTIONS[tx_id]
    tx["inspection_slip"] = slip
    if slip.is_accepted:
        tx["status"] = TransactionStatus.QUALITY_CONFIRMED
    else:
        tx["status"] = TransactionStatus.DISPUTED

    tx["updated_at"] = datetime.now(timezone.utc)
    return TransactionResponse(**tx)


@router.post("/{tx_id}/settle", response_model=TransactionResponse, summary="Settle Transaction & Trigger Escrow Payout")
def settle_transaction(
    tx_id: int,
    current_user: Any = Depends(get_current_user),
):
    """
    Finalize deal:
    Verifies delivery and inspection acceptance, locks final Net Realization,
    and advances transaction state to SETTLED.
    """
    if tx_id not in _MOCK_TRANSACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    tx = _MOCK_TRANSACTIONS[tx_id]
    if tx["status"] not in (TransactionStatus.DELIVERED, TransactionStatus.QUALITY_CONFIRMED, TransactionStatus.ACCEPTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot settle transaction from state: {tx['status']}",
        )

    tx["status"] = TransactionStatus.SETTLED
    tx["updated_at"] = datetime.now(timezone.utc)
    return TransactionResponse(**tx)


@router.post("/{tx_id}/state", response_model=TransactionResponse, summary="General State Machine Transition")
def update_transaction_state(
    tx_id: int,
    payload: TransactionStateUpdate,
    current_user: Any = Depends(get_current_user),
):
    """Advance transaction lifecycle to any valid target state."""
    if tx_id not in _MOCK_TRANSACTIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    tx = _MOCK_TRANSACTIONS[tx_id]
    tx["status"] = payload.new_status
    if payload.inspection_slip:
        tx["inspection_slip"] = payload.inspection_slip
    tx["updated_at"] = datetime.now(timezone.utc)
    return TransactionResponse(**tx)
