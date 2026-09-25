"""
Commodity Lots and FPO Bulk Aggregation Router for KrishiDisha.
Supports digital lot creation, quality parameter inspection,
filtering by moisture/distance, and bulk lot aggregation with sub-lot traceability.
"""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.lot_schema import (
    OwnerType,
    LotStatus,
    QualityGrade,
    StorageState,
    LotCreate,
    LotUpdate,
    LotResponse,
    SubLotContribution,
    BulkLotCreate,
    AggregatedLotResponse,
    LotFilterParams,
)
from app.schemas.auth_schema import UserRole

# Dependencies
from app.routes.auth import get_db, get_current_user, require_role

# Models
try:
    from app.models.lot import Lot, SubLotContribution as SubLotModel
    from app.models.market import Commodity
    from app.models.user import User, Farmer, FPO
except ImportError:
    Lot = SubLotModel = Commodity = User = Farmer = FPO = None

router = APIRouter(prefix="/lots", tags=["Lots & Aggregation"])

# ==========================================
# In-Memory Mock Store (Demonstration Data)
# ==========================================
_MOCK_LOTS: Dict[int, Dict[str, Any]] = {
    101: {
        "id": 101,
        "owner_type": OwnerType.FARMER,
        "owner_id": 1,
        "owner_name": "Ramesh Chandra Patel",
        "parent_bulk_lot_id": None,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati",
        "quantity_quintals": 65.0,
        "quality_grade": QualityGrade.GRADE_A,
        "moisture_pct": 11.2,
        "storage_state": StorageState.FARM_STORED,
        "location_address": "Village Nagda, Tehsil Badnagar, District Ujjain, MP",
        "location_lat": 23.4542,
        "location_lng": 75.4168,
        "harvest_date": date(2026, 3, 10),
        "expected_selling_window_start": date(2026, 3, 15),
        "expected_selling_window_end": date(2026, 4, 15),
        "minimum_acceptable_price": 2450.0,
        "status": LotStatus.ACTIVE,
        "created_at": datetime(2026, 3, 11, 10, 0, 0, tzinfo=timezone.utc),
        "updated_at": None,
    },
    102: {
        "id": 102,
        "owner_type": OwnerType.FARMER,
        "owner_id": 1,
        "owner_name": "Ramesh Chandra Patel",
        "parent_bulk_lot_id": None,
        "commodity_id": 2,
        "commodity_name": "Soybean (Yellow)",
        "variety": "JS-335",
        "quantity_quintals": 45.0,
        "quality_grade": QualityGrade.FAQ,
        "moisture_pct": 11.8,
        "storage_state": StorageState.WAREHOUSE,
        "location_address": "Nagda Rural Warehouse, Ujjain, MP",
        "location_lat": 23.4510,
        "location_lng": 75.4210,
        "harvest_date": date(2026, 3, 5),
        "expected_selling_window_start": date(2026, 3, 10),
        "expected_selling_window_end": date(2026, 4, 5),
        "minimum_acceptable_price": 4300.0,
        "status": LotStatus.ACTIVE,
        "created_at": datetime(2026, 3, 6, 11, 30, 0, tzinfo=timezone.utc),
        "updated_at": None,
    },
    103: {
        "id": 103,
        "owner_type": OwnerType.FPO,
        "owner_id": 2,
        "owner_name": "Ujjain Kisan Samriddhi Agro Producer Co.",
        "parent_bulk_lot_id": None,
        "commodity_id": 1,
        "commodity_name": "Wheat (Sharbati)",
        "variety": "Sharbati Premium",
        "quantity_quintals": 520.0,
        "quality_grade": QualityGrade.GRADE_A,
        "moisture_pct": 10.9,
        "storage_state": StorageState.WAREHOUSE,
        "location_address": "FPO Central Hub, Industrial Area, Ujjain, MP",
        "location_lat": 23.1765,
        "location_lng": 75.7885,
        "harvest_date": date(2026, 3, 8),
        "expected_selling_window_start": date(2026, 3, 12),
        "expected_selling_window_end": date(2026, 4, 20),
        "minimum_acceptable_price": 2580.0,
        "status": LotStatus.ACTIVE,
        "created_at": datetime(2026, 3, 12, 9, 15, 0, tzinfo=timezone.utc),
        "updated_at": None,
    },
}

_MOCK_AGGREGATIONS: Dict[int, List[Dict[str, Any]]] = {
    103: [
        {
            "child_lot_id": 101,
            "farmer_id": 1,
            "farmer_name": "Ramesh Chandra Patel",
            "farmer_phone": "9876543210",
            "quantity_quintals": 65.0,
            "moisture_pct": 11.2,
            "quality_grade": QualityGrade.GRADE_A,
            "contribution_share_pct": 12.5,
        },
        {
            "child_lot_id": 104,
            "farmer_id": 4,
            "farmer_name": "Suresh Verma",
            "farmer_phone": "9876543214",
            "quantity_quintals": 120.0,
            "moisture_pct": 10.8,
            "quality_grade": QualityGrade.GRADE_A,
            "contribution_share_pct": 23.08,
        },
        {
            "child_lot_id": 105,
            "farmer_id": 5,
            "farmer_name": "Mahesh Patidar",
            "farmer_phone": "9876543215",
            "quantity_quintals": 335.0,
            "moisture_pct": 10.85,
            "quality_grade": QualityGrade.GRADE_A,
            "contribution_share_pct": 64.42,
        },
    ]
}


# ==========================================
# Route Handlers
# ==========================================

@router.post("", response_model=LotResponse, status_code=status.HTTP_201_CREATED, summary="Create Digital Lot Listing")
def create_lot(
    payload: LotCreate,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Create a new agricultural lot listing.
    Accessible by FARMER and FPO roles.
    """
    user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id", 1)
    user_role = getattr(current_user, "role", None) or current_user.get("role", UserRole.FARMER)
    owner_type = OwnerType.FPO if str(user_role) in ("FPO", UserRole.FPO.value) else OwnerType.FARMER
    user_name = getattr(current_user, "full_name", None) or current_user.get("full_name", "Farmer")

    if db is not None and Lot is not None:
        db_lot = Lot(
            owner_type=owner_type.value,
            owner_id=user_id,
            commodity_id=payload.commodity_id,
            variety=payload.variety,
            quantity_quintals=payload.quantity_quintals,
            quality_grade=payload.quality_grade.value,
            moisture_pct=payload.moisture_pct,
            storage_state=payload.storage_state.value,
            location_address=payload.location_address,
            location_lat=payload.location_lat,
            location_lng=payload.location_lng,
            harvest_date=payload.harvest_date,
            expected_selling_window_start=payload.expected_selling_window_start,
            expected_selling_window_end=payload.expected_selling_window_end,
            minimum_acceptable_price=payload.minimum_acceptable_price,
            status=LotStatus.ACTIVE.value,
        )
        db.add(db_lot)
        db.commit()
        db.refresh(db_lot)
        return db_lot

    # In-memory mock
    new_id = max(_MOCK_LOTS.keys(), default=100) + 1
    new_lot = {
        "id": new_id,
        "owner_type": owner_type,
        "owner_id": user_id,
        "owner_name": user_name,
        "parent_bulk_lot_id": None,
        "commodity_id": payload.commodity_id,
        "commodity_name": payload.commodity_name or "Wheat",
        "variety": payload.variety,
        "quantity_quintals": payload.quantity_quintals,
        "quality_grade": payload.quality_grade,
        "moisture_pct": payload.moisture_pct,
        "storage_state": payload.storage_state,
        "location_address": payload.location_address,
        "location_lat": payload.location_lat,
        "location_lng": payload.location_lng,
        "harvest_date": payload.harvest_date,
        "expected_selling_window_start": payload.expected_selling_window_start,
        "expected_selling_window_end": payload.expected_selling_window_end,
        "minimum_acceptable_price": payload.minimum_acceptable_price,
        "status": LotStatus.ACTIVE,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    _MOCK_LOTS[new_id] = new_lot
    return new_lot


@router.get("", response_model=List[LotResponse], summary="Query Active Lots with Filters")
def list_lots(
    commodity_id: Optional[int] = Query(None, description="Filter by commodity ID"),
    quality_grade: Optional[QualityGrade] = Query(None, description="Filter by grade (GRADE_A, GRADE_B, FAQ)"),
    max_moisture: Optional[float] = Query(None, description="Filter lots with moisture <= threshold"),
    min_quantity: Optional[float] = Query(None, description="Filter lots with quantity >= threshold"),
    owner_type: Optional[OwnerType] = Query(None, description="Filter by owner type (FARMER, FPO)"),
    status_filter: Optional[LotStatus] = Query(LotStatus.ACTIVE, alias="status"),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve active lots available on the KrishiDisha digital exchange.
    Supports multi-attribute agricultural quality filtering.
    """
    if db is not None and Lot is not None:
        query = db.query(Lot)
        if status_filter:
            query = query.filter(Lot.status == status_filter.value)
        if commodity_id:
            query = query.filter(Lot.commodity_id == commodity_id)
        if quality_grade:
            query = query.filter(Lot.quality_grade == quality_grade.value)
        if max_moisture:
            query = query.filter(Lot.moisture_pct <= max_moisture)
        if min_quantity:
            query = query.filter(Lot.quantity_quintals >= min_quantity)
        if owner_type:
            query = query.filter(Lot.owner_type == owner_type.value)
        return query.order_by(Lot.created_at.desc()).all()

    # Filter mock records
    results = []
    for lot in _MOCK_LOTS.values():
        if status_filter and lot["status"] != status_filter:
            continue
        if commodity_id and lot["commodity_id"] != commodity_id:
            continue
        if quality_grade and lot["quality_grade"] != quality_grade:
            continue
        if max_moisture and lot["moisture_pct"] > max_moisture:
            continue
        if min_quantity and lot["quantity_quintals"] < min_quantity:
            continue
        if owner_type and lot["owner_type"] != owner_type:
            continue
        results.append(lot)
    return results


@router.get("/{lot_id}", response_model=LotResponse, summary="Get Lot by ID")
def get_lot(lot_id: int, db: Optional[Session] = Depends(get_db)):
    """Retrieve full specifications and quality parameters of a single lot."""
    if db is not None and Lot is not None:
        lot = db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
        return lot

    if lot_id in _MOCK_LOTS:
        return _MOCK_LOTS[lot_id]

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")


@router.patch("/{lot_id}/status", response_model=LotResponse, summary="Update Lot Status")
def update_lot_status(
    lot_id: int,
    payload: LotUpdate,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """Update lot status (e.g. mark SOLD, RESERVED, or WITHDRAWN)."""
    if db is not None and Lot is not None:
        lot = db.query(Lot).filter(Lot.id == lot_id).first()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")
        if payload.status:
            lot.status = payload.status.value
        if payload.minimum_acceptable_price is not None:
            lot.minimum_acceptable_price = payload.minimum_acceptable_price
        db.commit()
        db.refresh(lot)
        return lot

    if lot_id in _MOCK_LOTS:
        lot = _MOCK_LOTS[lot_id]
        if payload.status:
            lot["status"] = payload.status
        if payload.minimum_acceptable_price is not None:
            lot["minimum_acceptable_price"] = payload.minimum_acceptable_price
        lot["updated_at"] = datetime.now(timezone.utc)
        return lot

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lot not found")


@router.post("/bulk-aggregate", response_model=AggregatedLotResponse, status_code=status.HTTP_201_CREATED, summary="FPO Bulk Lot Aggregation")
def bulk_aggregate_lots(
    payload: BulkLotCreate,
    current_user: Any = Depends(require_role(UserRole.FPO, UserRole.ADMIN)),
    db: Optional[Session] = Depends(get_db),
):
    """
    FPO Bulk Aggregation Engine:
    Combines compatible smallholder lots into a single master bulk lot,
    calculating weighted average moisture, volume share, and origin traceability.
    """
    fpo_id = getattr(current_user, "id", None) or current_user.get("id", 2)
    fpo_name = getattr(current_user, "full_name", None) or current_user.get("full_name", "FPO Federation")

    # In-memory validation & calculation
    child_lots = []
    for cid in payload.child_lot_ids:
        if cid in _MOCK_LOTS:
            child_lots.append(_MOCK_LOTS[cid])
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Child lot {cid} not found or invalid")

    total_volume = sum(c["quantity_quintals"] for c in child_lots)
    if total_volume <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Aggregated volume must be greater than zero")

    weighted_moisture = sum(c["moisture_pct"] * c["quantity_quintals"] for c in child_lots) / total_volume

    # Determine master grade
    all_grade_a = all(c["quality_grade"] == QualityGrade.GRADE_A for c in child_lots)
    master_grade = QualityGrade.GRADE_A if (all_grade_a and weighted_moisture <= 12.0) else QualityGrade.FAQ

    master_lot_id = max(_MOCK_LOTS.keys(), default=100) + 1

    # Build sub-lot traceability records
    contributions: List[SubLotContribution] = []
    for c in child_lots:
        share = round((c["quantity_quintals"] / total_volume) * 100.0, 2)
        contrib = SubLotContribution(
            child_lot_id=c["id"],
            farmer_id=c["owner_id"],
            farmer_name=c.get("owner_name", "Smallholder Farmer"),
            farmer_phone="9876543210",
            quantity_quintals=c["quantity_quintals"],
            moisture_pct=c["moisture_pct"],
            quality_grade=c["quality_grade"],
            contribution_share_pct=share,
        )
        contributions.append(contrib)
        c["status"] = LotStatus.AGGREGATED
        c["parent_bulk_lot_id"] = master_lot_id

    master_lot_record = {
        "id": master_lot_id,
        "owner_type": OwnerType.FPO,
        "owner_id": fpo_id,
        "owner_name": fpo_name,
        "parent_bulk_lot_id": None,
        "commodity_id": payload.commodity_id,
        "commodity_name": "Aggregated " + payload.variety,
        "variety": payload.variety,
        "quantity_quintals": round(total_volume, 2),
        "quality_grade": master_grade,
        "moisture_pct": round(weighted_moisture, 2),
        "storage_state": StorageState.WAREHOUSE,
        "location_address": payload.hub_address or "FPO Aggregation Hub",
        "location_lat": payload.aggregation_hub_lat,
        "location_lng": payload.aggregation_hub_lng,
        "harvest_date": date.today(),
        "expected_selling_window_start": date.today(),
        "expected_selling_window_end": None,
        "minimum_acceptable_price": payload.minimum_acceptable_price,
        "status": LotStatus.ACTIVE,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }

    _MOCK_LOTS[master_lot_id] = master_lot_record
    _MOCK_AGGREGATIONS[master_lot_id] = [c.model_dump() for c in contributions]

    return AggregatedLotResponse(
        **master_lot_record,
        sub_lots=contributions,
        total_contributing_farmers=len(contributions),
        weighted_average_moisture=round(weighted_moisture, 2),
    )


@router.get("/aggregated/{bulk_lot_id}", response_model=AggregatedLotResponse, summary="Get Aggregated Bulk Lot Traceability")
def get_aggregated_lot(bulk_lot_id: int):
    """Retrieve bulk lot with detailed smallholder sub-lot origin records."""
    if bulk_lot_id not in _MOCK_LOTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bulk lot not found")

    lot = _MOCK_LOTS[bulk_lot_id]
    raw_contribs = _MOCK_AGGREGATIONS.get(bulk_lot_id, [])
    contributions = [SubLotContribution(**rc) for rc in raw_contribs]

    weighted_moist = (
        sum(c.moisture_pct * c.quantity_quintals for c in contributions) / lot["quantity_quintals"]
        if contributions else lot["moisture_pct"]
    )

    return AggregatedLotResponse(
        **lot,
        sub_lots=contributions,
        total_contributing_farmers=len(contributions),
        weighted_average_moisture=round(weighted_moist, 2),
    )
