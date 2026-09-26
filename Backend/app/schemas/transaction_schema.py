"""
Digital Negotiation, Offers, and Transaction State Machine Pydantic Schemas
for KrishiDisha.
Supports offer negotiation cycles, contract lock, dispatch tracking,
weighment/inspection slips, and net realization settlement.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.lot_schema import QualityGrade


class OfferStatus(str, Enum):
    PENDING = "PENDING"
    COUNTERED = "COUNTERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TransactionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    LOT_RESERVED = "LOT_RESERVED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    QUALITY_CONFIRMED = "QUALITY_CONFIRMED"
    SETTLED = "SETTLED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class OfferInitiator(str, Enum):
    FARMER = "FARMER"
    FPO = "FPO"
    BUYER = "BUYER"


# ==========================================
# Digital Negotiation & Offer Schemas
# ==========================================

class OfferCreate(BaseModel):
    lot_id: Optional[int] = Field(default=None, description="Target digital lot ID (if offering on a lot)")
    requirement_id: Optional[int] = Field(default=None, description="Target buyer tender requirement ID (if reverse bidding)")
    offered_price_per_quintal: float = Field(..., gt=0.0, description="Offered price per quintal in INR")
    quantity_quintals: float = Field(..., gt=0.0, description="Volume offered in Quintals")
    delivery_terms: Optional[str] = Field(default="EX_FARM", description="EX_FARM (buyer arranges transport) or DELIVERED_DESTINATION")
    proposed_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class CounterOfferRequest(BaseModel):
    counter_price_per_quintal: float = Field(..., gt=0.0, description="Updated counter price per quintal in INR")
    counter_quantity_quintals: Optional[float] = Field(default=None, gt=0.0, description="Optional updated counter volume")
    counter_notes: Optional[str] = None


class OfferResponse(BaseModel):
    id: int
    lot_id: Optional[int] = None
    requirement_id: Optional[int] = None
    buyer_id: int
    buyer_name: str
    seller_id: int
    seller_name: str
    offered_price_per_quintal: float
    quantity_quintals: float
    counter_price_per_quintal: Optional[float] = None
    status: OfferStatus
    last_acted_by: OfferInitiator
    delivery_terms: Optional[str] = "EX_FARM"
    proposed_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Transaction Schemas & Delivery Confirmation
# ==========================================

class QualityInspectionSlip(BaseModel):
    inspected_quantity_quintals: float = Field(..., gt=0.0, description="Actual scale weight recorded at receiving hub")
    measured_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Physical laboratory/meter moisture reading")
    measured_foreign_matter_pct: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    confirmed_grade: QualityGrade
    inspector_name: Optional[str] = None
    weight_slip_no: Optional[str] = None
    is_accepted: bool = True
    rejection_reason: Optional[str] = None


class TransactionCreate(BaseModel):
    offer_id: int = Field(..., description="ID of accepted offer to lock into contract")
    agreed_price_per_quintal: float = Field(..., gt=0.0)
    agreed_quantity_quintals: float = Field(..., gt=0.0)
    transport_cost: float = Field(default=0.0, ge=0.0, description="Estimated or agreed freight cost")
    storage_cost: float = Field(default=0.0, ge=0.0, description="Accrued storage fees")
    handling_cost: float = Field(default=0.0, ge=0.0, description="Loading/unloading/mandi cess")
    notes: Optional[str] = None


class TransactionStateUpdate(BaseModel):
    new_status: TransactionStatus
    remarks: Optional[str] = None
    proof_document_url: Optional[str] = Field(default=None, description="Weighment slip or consignment note link")
    inspection_slip: Optional[QualityInspectionSlip] = None


class TransactionResponse(BaseModel):
    id: int
    offer_id: int
    lot_id: Optional[int] = None
    seller_id: int
    seller_name: str
    buyer_id: int
    buyer_name: str
    commodity_name: str
    agreed_price_per_quintal: float
    agreed_quantity_quintals: float
    gross_revenue: float = Field(..., description="Quantity * Agreed Price")
    transport_cost: float = 0.0
    storage_cost: float = 0.0
    handling_cost: float = 0.0
    net_realization: float = Field(..., description="Gross - Transport - Storage - Handling")
    status: TransactionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    inspection_slip: Optional[QualityInspectionSlip] = None

    model_config = ConfigDict(from_attributes=True)
