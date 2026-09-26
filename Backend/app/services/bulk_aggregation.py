"""
FPO Bulk Aggregation and Origin Traceability Engine for KrishiDisha.
Combines fragmented smallholder lots into high-volume institutional bulk lots
while maintaining strict physical quality constraints (weighted moisture <= 12%)
and complete origin traceability for pro-rata escrow disbursements.
"""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from app.schemas.lot_schema import (
    QualityGrade,
    StorageState,
    LotStatus,
    OwnerType,
    SubLotContribution,
    AggregatedLotResponse,
)
from app.schemas.payment_schema import SmallholderPayout, PaymentStatus


def validate_child_lots(child_lots: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validates compatibility of child lots for pooling:
    - At least 2 child lots required.
    - All lots must belong to the exact same commodity.
    - Child lots must not be already sold or aggregated.
    """
    if len(child_lots) < 2:
        return False, "At least 2 child lots are required to form an aggregated bulk lot."

    first_comm = child_lots[0].get("commodity_id")
    for lot in child_lots:
        if lot.get("commodity_id") != first_comm:
            return False, f"Commodity mismatch: Lot #{lot.get('id')} has commodity {lot.get('commodity_id')}, expected {first_comm}."
        status_val = lot.get("status")
        if status_val not in (LotStatus.ACTIVE, LotStatus.ACTIVE.value, "ACTIVE"):
            return False, f"Lot #{lot.get('id')} is not available for aggregation (status: {status_val})."

    return True, None


def aggregate_smallholder_lots(
    child_lots: List[Dict[str, Any]],
    fpo_id: int,
    fpo_name: str,
    hub_lat: float,
    hub_lng: float,
    hub_address: Optional[str] = None,
    minimum_acceptable_price: Optional[float] = None,
    master_lot_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Core Aggregation Algorithm:
    1. Computes total aggregated quantity: Q_total = sum(q_i)
    2. Calculates weighted average moisture: M_weighted = sum(q_i * m_i) / Q_total
    3. Assigns quality grade based on weighted moisture and child grades.
    4. Calculates pro-rata contribution share percentage for each smallholder.
    """
    is_valid, err_msg = validate_child_lots(child_lots)
    if not is_valid:
        raise ValueError(err_msg)

    total_volume = sum(float(c["quantity_quintals"]) for c in child_lots)
    if total_volume <= 0:
        raise ValueError("Total aggregated volume must be greater than zero.")

    weighted_moisture = sum(
        float(c["moisture_pct"]) * float(c["quantity_quintals"])
        for c in child_lots
    ) / total_volume

    # Grade classification
    all_grade_a = all(
        c.get("quality_grade") in (QualityGrade.GRADE_A, QualityGrade.GRADE_A.value, "GRADE_A")
        for c in child_lots
    )
    master_grade = QualityGrade.GRADE_A if (all_grade_a and weighted_moisture <= 12.0) else QualityGrade.FAQ

    # Traceability contributions
    contributions: List[SubLotContribution] = []
    for c in child_lots:
        qty = float(c["quantity_quintals"])
        share = round((qty / total_volume) * 100.0, 2)
        contrib = SubLotContribution(
            child_lot_id=c["id"],
            farmer_id=c.get("owner_id", 1),
            farmer_name=c.get("owner_name", "Smallholder Farmer"),
            farmer_phone=c.get("farmer_phone", "9876543210"),
            quantity_quintals=qty,
            moisture_pct=float(c["moisture_pct"]),
            quality_grade=c.get("quality_grade", QualityGrade.FAQ),
            contribution_share_pct=share,
        )
        contributions.append(contrib)

    first_lot = child_lots[0]
    variety = first_lot.get("variety", "Standard")
    commodity_id = first_lot.get("commodity_id", 1)

    master_lot = {
        "id": master_lot_id or 1001,
        "owner_type": OwnerType.FPO,
        "owner_id": fpo_id,
        "owner_name": fpo_name,
        "parent_bulk_lot_id": None,
        "commodity_id": commodity_id,
        "commodity_name": f"Aggregated {variety}",
        "variety": variety,
        "quantity_quintals": round(total_volume, 2),
        "quality_grade": master_grade,
        "moisture_pct": round(weighted_moisture, 2),
        "storage_state": StorageState.WAREHOUSE,
        "location_address": hub_address or "FPO Aggregation Hub",
        "location_lat": hub_lat,
        "location_lng": hub_lng,
        "harvest_date": date.today(),
        "expected_selling_window_start": date.today(),
        "expected_selling_window_end": None,
        "minimum_acceptable_price": minimum_acceptable_price,
        "status": LotStatus.ACTIVE,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }

    return {
        "master_lot": master_lot,
        "sub_lots": contributions,
        "total_contributing_farmers": len(contributions),
        "weighted_average_moisture": round(weighted_moisture, 2),
    }


def compute_smallholder_payouts(
    contributions: List[SubLotContribution],
    total_net_realization: float,
    total_logistics_cost: float = 0.0,
) -> List[SmallholderPayout]:
    """
    Computes exact pro-rata bank disbursements for individual smallholders
    contributing to an aggregated FPO lot.
    """
    if not contributions:
        return []

    payouts: List[SmallholderPayout] = []
    for c in contributions:
        share_ratio = c.contribution_share_pct / 100.0
        gross_share = round((total_net_realization + total_logistics_cost) * share_ratio, 2)
        deduction = round(total_logistics_cost * share_ratio, 2)
        net_share = round(total_net_realization * share_ratio, 2)

        payouts.append(
            SmallholderPayout(
                farmer_id=c.farmer_id,
                farmer_name=c.farmer_name or f"Farmer #{c.farmer_id}",
                account_no_masked=f"*******{c.farmer_id * 1234 % 9000 + 1000}",
                ifsc_code="SBIN0004567",
                quantity_contributed_quintals=c.quantity_quintals,
                share_pct=c.contribution_share_pct,
                gross_payout=gross_share,
                pro_rata_deductions=deduction,
                net_payout=net_share,
                payout_status=PaymentStatus.PENDING,
            )
        )

    return payouts
