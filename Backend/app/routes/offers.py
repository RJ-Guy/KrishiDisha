"""
Digital Negotiation and Offers Router for KrishiDisha.
Supports offer initiation, counter-bidding cycles, and offer acceptance
which automatically locks terms and creates a binding Transaction.
"""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.transaction_schema import (
    OfferStatus,
    OfferInitiator,
    OfferCreate,
    CounterOfferRequest,
    OfferResponse,
    TransactionResponse,
    TransactionStatus,
)
from app.schemas.auth_schema import UserRole

# Dependencies
from app.routes.auth import get_db, get_current_user

# Models
try:
    from app.models.transaction import Offer, Transaction
    from app.models.lot import Lot
except ImportError:
    Offer = Transaction = Lot = None

router = APIRouter(prefix="/offers", tags=["Negotiation & Offers"])

# ==========================================
# In-Memory Demonstration Store
# ==========================================
_MOCK_OFFERS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "lot_id": 101,
        "requirement_id": 1,
        "buyer_id": 1,
        "buyer_name": "ITC Limited Agri Business (e-Choupal)",
        "seller_id": 1,
        "seller_name": "Ramesh Chandra Patel",
        "offered_price_per_quintal": 2620.0,
        "quantity_quintals": 65.0,
        "counter_price_per_quintal": None,
        "status": OfferStatus.PENDING,
        "last_acted_by": OfferInitiator.BUYER,
        "delivery_terms": "EX_FARM",
        "proposed_delivery_date": date.today(),
        "notes": "Direct farmgate pickup with digital weighment slip.",
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    },
    2: {
        "id": 2,
        "lot_id": 103,
        "requirement_id": 1,
        "buyer_id": 1,
        "buyer_name": "ITC Limited Agri Business (e-Choupal)",
        "seller_id": 2,
        "seller_name": "Ujjain Kisan Samriddhi Agro Producer Co.",
        "offered_price_per_quintal": 2650.0,
        "quantity_quintals": 500.0,
        "counter_price_per_quintal": 2680.0,
        "status": OfferStatus.COUNTERED,
        "last_acted_by": OfferInitiator.FPO,
        "delivery_terms": "DELIVERED_DESTINATION",
        "proposed_delivery_date": date.today(),
        "notes": "FPO aggregated premium lot. Counter-offered ₹2,680/Q.",
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    },
}

# Shared transactions store importable by transactions.py
_MOCK_TRANSACTIONS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "offer_id": 100,
        "lot_id": 101,
        "seller_id": 1,
        "seller_name": "Ramesh Chandra Patel",
        "buyer_id": 1,
        "buyer_name": "ITC Limited Agri Business",
        "commodity_name": "Wheat (Sharbati)",
        "agreed_price_per_quintal": 2600.0,
        "agreed_quantity_quintals": 65.0,
        "gross_revenue": 169000.0,  # 65 * 2600
        "transport_cost": 2100.0,
        "storage_cost": 650.0,
        "handling_cost": 500.0,
        "net_realization": 165750.0,  # 169000 - 3250
        "status": TransactionStatus.ACCEPTED,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "inspection_slip": None,
    }
}


# ==========================================
# Route Handlers
# ==========================================

@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED, summary="Submit Digital Offer")
def submit_offer(
    payload: OfferCreate,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Submit a binding digital bid/offer on a lot or institutional tender.
    Can be initiated by Buyer, Farmer, or FPO.
    """
    user_id = getattr(current_user, "id", None) or current_user.get("id", 1)
    user_name = getattr(current_user, "full_name", None) or current_user.get("full_name", "User")
    user_role = getattr(current_user, "role", None) or current_user.get("role", "BUYER")

    if str(user_role) in ("BUYER", UserRole.BUYER.value):
        buyer_id = 1
        buyer_name = user_name
        seller_id = 1
        seller_name = "Farmer / Seller"
        initiator = OfferInitiator.BUYER
    elif str(user_role) in ("FPO", UserRole.FPO.value):
        buyer_id = 1
        buyer_name = "Institutional Buyer"
        seller_id = user_id
        seller_name = user_name
        initiator = OfferInitiator.FPO
    else:
        buyer_id = 1
        buyer_name = "Institutional Buyer"
        seller_id = user_id
        seller_name = user_name
        initiator = OfferInitiator.FARMER

    new_id = max(_MOCK_OFFERS.keys(), default=0) + 1
    new_offer = {
        "id": new_id,
        "lot_id": payload.lot_id,
        "requirement_id": payload.requirement_id,
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "seller_id": seller_id,
        "seller_name": seller_name,
        "offered_price_per_quintal": payload.offered_price_per_quintal,
        "quantity_quintals": payload.quantity_quintals,
        "counter_price_per_quintal": None,
        "status": OfferStatus.PENDING,
        "last_acted_by": initiator,
        "delivery_terms": payload.delivery_terms or "EX_FARM",
        "proposed_delivery_date": payload.proposed_delivery_date,
        "notes": payload.notes,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    _MOCK_OFFERS[new_id] = new_offer
    return OfferResponse(**new_offer)


@router.get("", response_model=List[OfferResponse], summary="List User Offers")
def list_offers(
    status_filter: Optional[OfferStatus] = Query(None, alias="status"),
    current_user: Any = Depends(get_current_user),
):
    """Retrieve all digital negotiation offers involving the current user."""
    user_id = getattr(current_user, "id", None) or current_user.get("id", 1)
    results = []
    for offer in _MOCK_OFFERS.values():
        if status_filter and offer["status"] != status_filter:
            continue
        results.append(OfferResponse(**offer))
    return results


@router.get("/{offer_id}", response_model=OfferResponse, summary="Get Offer Details")
def get_offer(offer_id: int):
    """Retrieve details and negotiation history of an offer."""
    if offer_id not in _MOCK_OFFERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return OfferResponse(**_MOCK_OFFERS[offer_id])


@router.post("/{offer_id}/counter", response_model=OfferResponse, summary="Submit Counter-Offer")
def counter_offer(
    offer_id: int,
    payload: CounterOfferRequest,
    current_user: Any = Depends(get_current_user),
):
    """Submit counter-bid with updated price per quintal or volume."""
    if offer_id not in _MOCK_OFFERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    offer = _MOCK_OFFERS[offer_id]
    if offer["status"] in (OfferStatus.ACCEPTED, OfferStatus.REJECTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot counter an accepted or rejected offer")

    offer["counter_price_per_quintal"] = payload.counter_price_per_quintal
    if payload.counter_quantity_quintals:
        offer["quantity_quintals"] = payload.counter_quantity_quintals
    if payload.counter_notes:
        offer["notes"] = payload.counter_notes

    offer["status"] = OfferStatus.COUNTERED
    offer["updated_at"] = datetime.now(timezone.utc)
    return OfferResponse(**offer)


@router.post("/{offer_id}/accept", response_model=TransactionResponse, summary="Accept Offer & Lock Binding Contract")
def accept_offer(
    offer_id: int,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Accept an offer or counter-offer:
    Locks agreed terms and automatically initializes a binding Transaction
    with gross revenue, estimated freight/storage/handling deductions,
    and expected Net Realization.
    """
    if offer_id not in _MOCK_OFFERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    offer = _MOCK_OFFERS[offer_id]
    if offer["status"] == OfferStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer is already accepted")

    offer["status"] = OfferStatus.ACCEPTED
    offer["updated_at"] = datetime.now(timezone.utc)

    agreed_price = offer["counter_price_per_quintal"] or offer["offered_price_per_quintal"]
    quantity = offer["quantity_quintals"]
    gross = agreed_price * quantity

    # Deductions: transport estimated at ₹35/Q, storage ₹10/Q, handling ₹8/Q
    est_transport = round(quantity * 35.0, 2)
    est_storage = round(quantity * 10.0, 2)
    est_handling = round(quantity * 8.0, 2)
    net_realization = round(gross - est_transport - est_storage - est_handling, 2)

    new_tx_id = max(_MOCK_TRANSACTIONS.keys(), default=0) + 1
    new_tx = {
        "id": new_tx_id,
        "offer_id": offer_id,
        "lot_id": offer.get("lot_id"),
        "seller_id": offer["seller_id"],
        "seller_name": offer["seller_name"],
        "buyer_id": offer["buyer_id"],
        "buyer_name": offer["buyer_name"],
        "commodity_name": "Wheat (Sharbati)",
        "agreed_price_per_quintal": agreed_price,
        "agreed_quantity_quintals": quantity,
        "gross_revenue": gross,
        "transport_cost": est_transport,
        "storage_cost": est_storage,
        "handling_cost": est_handling,
        "net_realization": net_realization,
        "status": TransactionStatus.ACCEPTED,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "inspection_slip": None,
    }
    _MOCK_TRANSACTIONS[new_tx_id] = new_tx
    return TransactionResponse(**new_tx)


@router.post("/{offer_id}/reject", response_model=OfferResponse, summary="Reject Offer")
def reject_offer(offer_id: int):
    """Reject an active offer or counter-offer."""
    if offer_id not in _MOCK_OFFERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    offer = _MOCK_OFFERS[offer_id]
    offer["status"] = OfferStatus.REJECTED
    offer["updated_at"] = datetime.now(timezone.utc)
    return OfferResponse(**offer)
