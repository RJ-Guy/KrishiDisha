"""
Database Seeding and Kaggle Dataset Ingestion Pipeline for KrishiDisha.
Supports:
1. Automated Kaggle / Agmarknet CSV dataset ingestion from data/raw/
   (Compatible with "Price of Agricultural Commodities in India" & Agmarknet feeds).
2. Complete Hackathon Demonstration Scenario Seeding matching SIH 2026 pitch deck:
   - Users (Farmer Ramesh Patel, Ujjain Kisan FPO, ITC Agri Business, Adani Wilmar)
   - Commodities (Sharbati Wheat, Yellow Soybean, Chana, Mustard)
   - APMC Mandis (Ujjain Chimanganj, Indore Laxmi Bai Nagar, Dewas, Badnagar)
   - MSP Centers (FCI Silo, NAFED Procurement)
   - Certified Warehouses (MPSWC, NCML)
   - Active Digital Lots with Sub-Lot Contribution Traceability
   - Institutional Reverse Procurement Tenders
   - Historical Mandi Price Time Series (60 days)
   - Active Offer, Transaction State Machine, Logistics, and Escrow Payments.
3. Offline Resilience: Automatically generates realistic baseline data if CSV not present.
"""

import os
import csv
import glob
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, init_db, engine
from app.models import (
    Base,
    User,
    Farmer,
    FPO,
    Buyer,
    BuyerRequirement,
    Commodity,
    Market,
    MarketPrice,
    ProcurementOption,
    StorageOption,
    Forecast,
    Lot,
    SubLotContribution,
    Offer,
    Transaction,
    Logistics,
    Payment,
    Grievance,
)
from app.routes.auth import hash_password

logger = logging.getLogger("krishidisha.database.seed")

# Known APMC Mandi GPS Coordinates (Malwa / Central India Cluster)
MANDI_COORDINATES = {
    "ujjain": (23.2014, 75.7947),
    "indore": (22.7533, 75.8637),
    "dewas": (22.9676, 76.0534),
    "badnagar": (23.0634, 75.3857),
    "nagda": (23.4542, 75.4168),
    "ratlam": (23.3315, 75.0367),
    "mandsaur": (24.0728, 75.0683),
    "neemuch": (24.4720, 74.8720),
    "bhopal": (23.2599, 77.4126),
    "dhar": (22.5976, 75.3040),
}


def _get_mandi_coords(mandi_name: str, default_lat: float = 23.2014, default_lng: float = 75.7947):
    """Fuzzy lookup for APMC mandi GPS coordinates."""
    name_lower = mandi_name.lower()
    for key, coords in MANDI_COORDINATES.items():
        if key in name_lower:
            return coords
    return default_lat, default_lng


def _parse_date(date_str: str) -> date:
    """Robust date parsing for diverse Kaggle CSV date formats."""
    date_str = date_str.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return date.today()


def _clean_price(val: Any, default: float = 2000.0) -> float:
    """Cleans currency string/float into numeric float."""
    if val is None:
        return default
    try:
        val_str = str(val).replace(",", "").replace("₹", "").replace("$", "").strip()
        return float(val_str)
    except ValueError:
        return default


# ==========================================
# 1. Kaggle CSV Ingestion Routine
# ==========================================
def ingest_kaggle_mandi_csv(
    db: Session,
    raw_dir: str = "data/raw",
    max_records: int = 10000,
    target_states: Optional[List[str]] = None,
) -> int:
    """
    Scans data/raw/ for Kaggle CSV files:
    - Robust path resolution for raw_dir (relative to cwd or project root).
    - In-memory cached lookups for Commodities and Markets to maximize ingestion throughput.
    - Normalizes columns: State, District, Market/Mandi, Commodity, Variety, Date, Prices.
    - Populates commodities, markets, and market_prices tables.
    """
    # Robust raw_dir resolution
    resolved_raw_dir = raw_dir
    if not os.path.isdir(resolved_raw_dir):
        candidates = [
            os.path.join(os.getcwd(), raw_dir),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", raw_dir),
            os.path.join(os.getcwd(), "..", raw_dir),
            "data/raw",
            "../data/raw",
        ]
        for cand in candidates:
            if os.path.isdir(cand):
                resolved_raw_dir = cand
                break

    csv_files = glob.glob(os.path.join(resolved_raw_dir, "*.csv"))
    if not csv_files:
        logger.info(f"No CSV files found in {resolved_raw_dir}. Will use synthetic demonstration seed.")
        return 0

    total_ingested = 0
    target_states_lower = [s.lower() for s in target_states] if target_states else ["all"]

    # Pre-populate caches to avoid thousands of repetitive round-trip queries
    comm_cache = {c.name.strip().lower(): c for c in db.query(Commodity).all()}
    mkt_cache = {(m.market_name.strip().lower(), m.state.strip().lower()): m for m in db.query(Market).all()}

    for file_path in csv_files:
        logger.info(f"Ingesting Kaggle dataset from {file_path}...")
        try:
            with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                # Normalize header names (lowercase, stripped)
                field_map = {k.strip().lower(): k for k in reader.fieldnames or []}

                state_col = next((field_map[k] for k in field_map if "state" in k), None)
                dist_col = next((field_map[k] for k in field_map if "district" in k), None)
                mkt_col = next((field_map[k] for k in field_map if "market" in k or "mandi" in k), None)
                comm_col = next((field_map[k] for k in field_map if "commodity" in k or "crop" in k), None)
                var_col = next((field_map[k] for k in field_map if "variety" in k), None)
                date_col = next((field_map[k] for k in field_map if "date" in k or "arrival_date" in k), None)
                modal_col = next((field_map[k] for k in field_map if "modal" in k), None)
                min_col = next((field_map[k] for k in field_map if "min" in k), None)
                max_col = next((field_map[k] for k in field_map if "max" in k), None)
                vol_col = next((field_map[k] for k in field_map if "arrival" in k and "date" not in k), None)

                if not (mkt_col and comm_col and modal_col):
                    logger.warning(f"File {file_path} lacks required columns (market, commodity, modal price). Skipping.")
                    continue

                batch_prices = []
                for row in reader:
                    if total_ingested >= max_records:
                        break

                    state_val = row.get(state_col, "Madhya Pradesh").strip() if state_col else "Madhya Pradesh"
                    if "all" not in target_states_lower and state_val.lower() not in target_states_lower:
                        continue

                    dist_val = row.get(dist_col, "General").strip() if dist_col else "General"
                    mkt_name = row.get(mkt_col, "").strip()
                    comm_name = row.get(comm_col, "").strip()
                    variety_val = row.get(var_col, "Standard").strip() if var_col else "Standard"

                    if not mkt_name or not comm_name:
                        continue

                    # 1. Commodity lookup/create using memory cache
                    comm_key = comm_name.lower()
                    comm = comm_cache.get(comm_key)
                    if not comm:
                        # Intelligent category categorization
                        category = "Agricultural Produce"
                        c_lower = comm_key
                        if any(w in c_lower for w in ["wheat", "paddy", "rice", "maize", "barley", "jowar", "bajra"]):
                            category = "Cereal"
                        elif any(w in c_lower for w in ["chana", "gram", "dal", "moong", "urad", "masoor", "arhar", "tur"]):
                            category = "Pulse"
                        elif any(w in c_lower for w in ["soybean", "mustard", "groundnut", "sunflower", "sesamum", "castor"]):
                            category = "Oilseed"
                        elif any(w in c_lower for w in ["mango", "apple", "banana", "orange", "grape", "papaya"]):
                            category = "Fruit"
                        elif any(w in c_lower for w in ["onion", "potato", "tomato", "chilli", "garlic", "ginger"]):
                            category = "Vegetable"

                        comm = Commodity(
                            name=comm_name,
                            category=category,
                            standard_unit="Quintal",
                        )
                        db.add(comm)
                        db.flush()
                        comm_cache[comm_key] = comm

                    # 2. Market lookup/create using memory cache
                    mkt_key = (mkt_name.lower(), state_val.lower())
                    mkt = mkt_cache.get(mkt_key)
                    if not mkt:
                        lat, lng = _get_mandi_coords(mkt_name)
                        mkt = Market(
                            market_name=mkt_name,
                            state=state_val,
                            district=dist_val,
                            latitude=lat,
                            longitude=lng,
                            is_apmc=True,
                        )
                        db.add(mkt)
                        db.flush()
                        mkt_cache[mkt_key] = mkt

                    # 3. Market Price Record
                    p_modal = _clean_price(row.get(modal_col), 2500.0)
                    p_min = _clean_price(row.get(min_col), p_modal - 80.0)
                    p_max = _clean_price(row.get(max_col), p_modal + 90.0)
                    arr_date = _parse_date(row.get(date_col, "")) if date_col else date.today()
                    vol = _clean_price(row.get(vol_col), 450.0) if vol_col else 450.0

                    m_price = MarketPrice(
                        market_id=mkt.id,
                        commodity_id=comm.id,
                        variety=variety_val,
                        arrival_date=arr_date,
                        min_price=p_min,
                        max_price=p_max,
                        modal_price=p_modal,
                        arrivals_volume_tonnes=vol,
                    )
                    batch_prices.append(m_price)
                    total_ingested += 1

                    if len(batch_prices) >= 500:
                        db.add_all(batch_prices)
                        db.commit()
                        batch_prices.clear()

                if batch_prices:
                    db.add_all(batch_prices)
                    db.commit()
                    batch_prices.clear()

                logger.info(f"Successfully ingested {total_ingested} records from {file_path}.")
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            db.rollback()

    return total_ingested


# ==========================================
# 2. Complete Hackathon Demonstration Seed
# ==========================================
def seed_demonstration_scenario(db: Session) -> None:
    """
    Seeds comprehensive SIH 2026 hackathon demo entities:
    - 4 Commodities, 4 Mandis, 3 Warehouses, 2 MSP Centers
    - 4 Pre-configured User Profiles (Farmer, FPO, Buyer, Admin)
    - Active Lots & FPO Aggregation with Sub-Lot Traceability
    - Institutional Tenders & Reverse Marketplace
    - 60-Day Historical Price Trajectories for UI charts
    - Accepted Transaction State Machine with Logistics & Escrow.
    """
    logger.info("Seeding SIH 2026 Hackathon Demonstration Scenario...")

    # ------------------------------------------
    # A. Commodities
    # ------------------------------------------
    commodities_data = [
        {"id": 1, "name": "Wheat (Sharbati)", "category": "Cereal", "standard_unit": "Quintal", "description": "Premium Sharbati Golden Grain Wheat"},
        {"id": 2, "name": "Soybean (Yellow)", "category": "Oilseed", "standard_unit": "Quintal", "description": "High oil-content Yellow Soybean (JS-335 / JS-9560)"},
        {"id": 3, "name": "Gram (Chana / Desi)", "category": "Pulse", "standard_unit": "Quintal", "description": "Malwa Desi Brown Chana"},
        {"id": 4, "name": "Mustard (Pusa Bold)", "category": "Oilseed", "standard_unit": "Quintal", "description": "High pungency Black Mustard Seed"},
    ]
    commodity_map = {}
    for c_data in commodities_data:
        c = db.query(Commodity).filter(Commodity.id == c_data["id"]).first()
        if not c:
            c = Commodity(**c_data)
            db.add(c)
            db.flush()
        commodity_map[c.id] = c

    # ------------------------------------------
    # B. Mandis / APMC Markets
    # ------------------------------------------
    mandis_data = [
        {"id": 1, "market_name": "Ujjain APMC Mandi (Chimanganj Mandi)", "state": "Madhya Pradesh", "district": "Ujjain", "latitude": 23.2014, "longitude": 75.7947, "is_apmc": True},
        {"id": 2, "market_name": "Indore Laxmi Bai Nagar APMC Mandi", "state": "Madhya Pradesh", "district": "Indore", "latitude": 22.7533, "longitude": 75.8637, "is_apmc": True},
        {"id": 3, "market_name": "Dewas APMC Mandi", "state": "Madhya Pradesh", "district": "Dewas", "latitude": 22.9676, "longitude": 76.0534, "is_apmc": True},
        {"id": 4, "market_name": "Badnagar Sub-Mandi Yard", "state": "Madhya Pradesh", "district": "Ujjain", "latitude": 23.0634, "longitude": 75.3857, "is_apmc": True},
    ]
    mandi_map = {}
    for m_data in mandis_data:
        m = db.query(Market).filter(Market.id == m_data["id"]).first()
        if not m:
            m = Market(**m_data)
            db.add(m)
            db.flush()
        mandi_map[m.id] = m

    # ------------------------------------------
    # C. Government MSP Procurement Centers
    # ------------------------------------------
    msp_data = [
        {"id": 1, "commodity_id": 1, "msp_price": 2275.0, "agency_name": "Food Corporation of India (FCI)", "center_location": "Ujjain Central Silo, MP", "state": "Madhya Pradesh", "district": "Ujjain", "latitude": 23.1950, "longitude": 75.8120, "active": True},
        {"id": 2, "commodity_id": 2, "msp_price": 4892.0, "agency_name": "NAFED State Procurement Center", "center_location": "Dewas Road Hub, Indore, MP", "state": "Madhya Pradesh", "district": "Indore", "latitude": 22.7680, "longitude": 75.8910, "active": True},
        {"id": 3, "commodity_id": 3, "msp_price": 5440.0, "agency_name": "NAFED Mandi Procurement Sub-Center", "center_location": "Ujjain APMC Complex, MP", "state": "Madhya Pradesh", "district": "Ujjain", "latitude": 23.2014, "longitude": 75.7947, "active": True},
    ]
    for p_data in msp_data:
        if not db.query(ProcurementOption).filter(ProcurementOption.id == p_data["id"]).first():
            db.add(ProcurementOption(**p_data))

    # ------------------------------------------
    # D. Licensed Warehouses & Cold Storages
    # ------------------------------------------
    storage_data = [
        {"id": 1, "facility_name": "MP State Warehousing & Logistics Corp (MPSWC) - Ujjain Hub", "state": "Madhya Pradesh", "district": "Ujjain", "daily_cost_per_quintal": 0.45, "capacity_quintals": 45000.0, "latitude": 23.1850, "longitude": 75.8010},
        {"id": 2, "facility_name": "National Collateral Management Services (NCML) Cold Chain", "state": "Madhya Pradesh", "district": "Indore", "daily_cost_per_quintal": 0.70, "capacity_quintals": 25000.0, "latitude": 22.7650, "longitude": 75.8850},
        {"id": 3, "facility_name": "Nagda Rural Agri Silos", "state": "Madhya Pradesh", "district": "Ujjain", "daily_cost_per_quintal": 0.40, "capacity_quintals": 10000.0, "latitude": 23.4480, "longitude": 75.4250},
    ]
    for s_data in storage_data:
        if not db.query(StorageOption).filter(StorageOption.id == s_data["id"]).first():
            db.add(StorageOption(**s_data))

    # ------------------------------------------
    # E. Users & Role Profiles
    # ------------------------------------------
    # 1. Farmer Ramesh Patel
    user_farmer = db.query(User).filter(User.phone == "9876543210").first()
    if not user_farmer:
        user_farmer = User(
            id=1,
            email="ramesh.farmer@krishidisha.in",
            phone="9876543210",
            password_hash=hash_password("farmer123"),
            full_name="Ramesh Chandra Patel",
            role="FARMER",
            language_preference="hi",
            is_active=True,
        )
        db.add(user_farmer)
        db.flush()
        db.add(Farmer(
            id=1,
            user_id=user_farmer.id,
            state="Madhya Pradesh",
            district="Ujjain",
            village="Nagda",
            pin_code="456335",
            land_size_acres=4.5,
            primary_crops=["Wheat", "Soybean", "Gram"],
        ))

    # 2. FPO Ujjain Kisan Samriddhi
    user_fpo = db.query(User).filter(User.phone == "9876543211").first()
    if not user_fpo:
        user_fpo = User(
            id=2,
            email="ujjain.kisan.fpo@krishidisha.in",
            phone="9876543211",
            password_hash=hash_password("fpo12345"),
            full_name="Ujjain Kisan Samriddhi FPO",
            role="FPO",
            language_preference="hi",
            is_active=True,
        )
        db.add(user_fpo)
        db.flush()
        db.add(FPO(
            id=1,
            user_id=user_fpo.id,
            organization_name="Ujjain Kisan Samriddhi Agro Producer Co.",
            registration_no="FPO-MP-UJJ-2024-0089",
            state="Madhya Pradesh",
            district="Ujjain",
            member_count=480,
            storage_capacity_quintals=12500.0,
        ))

    # 3. Buyer ITC Limited
    user_buyer_itc = db.query(User).filter(User.phone == "9876543212").first()
    if not user_buyer_itc:
        user_buyer_itc = User(
            id=3,
            email="procurement@itc-agri.com",
            phone="9876543212",
            password_hash=hash_password("buyer123"),
            full_name="ITC Agri Business Division",
            role="BUYER",
            language_preference="en",
            is_active=True,
        )
        db.add(user_buyer_itc)
        db.flush()
        db.add(Buyer(
            id=1,
            user_id=user_buyer_itc.id,
            company_name="ITC Limited Agri Business (e-Choupal)",
            gst_no="23AAACI1681G1Z0",
            trade_license="TL-MP-IND-88219",
            buyer_category="INSTITUTIONAL",
            reliability_score=98.5,
            verified=True,
            operating_states=["Madhya Pradesh", "Rajasthan", "Maharashtra"],
            on_time_payment_rate_pct=99.2,
            total_deals_completed=1420,
        ))

    # 4. Buyer Adani Wilmar
    user_buyer_adani = db.query(User).filter(User.phone == "9876543213").first()
    if not user_buyer_adani:
        user_buyer_adani = User(
            id=4,
            email="procurement@adaniwilmar.com",
            phone="9876543213",
            password_hash=hash_password("buyer123"),
            full_name="Adani Wilmar Procurement",
            role="BUYER",
            language_preference="en",
            is_active=True,
        )
        db.add(user_buyer_adani)
        db.flush()
        db.add(Buyer(
            id=2,
            user_id=user_buyer_adani.id,
            company_name="Adani Wilmar Ltd (Fortune Agro Hub)",
            gst_no="23AABCA1234F1Z5",
            trade_license="TL-MP-UJJ-44102",
            buyer_category="PROCESSOR",
            reliability_score=96.0,
            verified=True,
            operating_states=["Madhya Pradesh", "Gujarat"],
            on_time_payment_rate_pct=97.5,
            total_deals_completed=980,
        ))

    # 5. System Admin
    user_admin = db.query(User).filter(User.phone == "9876543299").first()
    if not user_admin:
        db.add(User(
            id=5,
            email="admin@krishidisha.in",
            phone="9876543299",
            password_hash=hash_password("admin2026"),
            full_name="KrishiDisha System Admin",
            role="ADMIN",
            language_preference="en",
            is_active=True,
        ))

    db.flush()

    # ------------------------------------------
    # F. Institutional Reverse Tenders
    # ------------------------------------------
    tenders_data = [
        {
            "id": 1,
            "buyer_id": 1,
            "commodity_id": 1,
            "variety": "Sharbati Premium",
            "required_quantity_quintals": 1000.0,
            "max_price_per_quintal": 2680.0,
            "min_grade": "GRADE_A",
            "max_moisture_pct": 11.5,
            "delivery_location_name": "ITC Procurement Hub, Dewas Naka, Indore, MP",
            "delivery_location_lat": 22.7712,
            "delivery_location_lng": 75.8941,
            "delivery_window_start": date.today(),
            "delivery_window_end": date.today() + timedelta(days=30),
            "special_conditions": "Moisture must be <= 11.5%. Digital weighment slip settlement within 24h.",
            "status": "OPEN",
            "fulfilled_quantity_quintals": 320.0,
        },
        {
            "id": 2,
            "buyer_id": 2,
            "commodity_id": 2,
            "variety": "JS-335",
            "required_quantity_quintals": 2500.0,
            "max_price_per_quintal": 4750.0,
            "min_grade": "FAQ",
            "max_moisture_pct": 12.0,
            "delivery_location_name": "Adani Wilmar Crushing Plant, Industrial Area, Ujjain, MP",
            "delivery_location_lat": 23.1812,
            "delivery_location_lng": 75.8105,
            "delivery_window_start": date.today(),
            "delivery_window_end": date.today() + timedelta(days=20),
            "special_conditions": "FPO aggregated bulk lots prioritized. Spot quality assessment.",
            "status": "OPEN",
            "fulfilled_quantity_quintals": 950.0,
        },
    ]
    for t_data in tenders_data:
        if not db.query(BuyerRequirement).filter(BuyerRequirement.id == t_data["id"]).first():
            db.add(BuyerRequirement(**t_data))

    # ------------------------------------------
    # G. Digital Lots & FPO Aggregation
    # ------------------------------------------
    lot_101 = db.query(Lot).filter(Lot.id == 101).first()
    if not lot_101:
        lot_101 = Lot(
            id=101,
            owner_type="FARMER",
            owner_id=1,
            commodity_id=1,
            variety="Sharbati",
            quantity_quintals=65.0,
            quality_grade="GRADE_A",
            moisture_pct=11.2,
            storage_state="FARM_STORED",
            location_address="Village Nagda, Tehsil Badnagar, District Ujjain, MP",
            location_lat=23.4542,
            location_lng=75.4168,
            harvest_date=date(2026, 3, 10),
            expected_selling_window_start=date(2026, 3, 15),
            expected_selling_window_end=date(2026, 4, 15),
            minimum_acceptable_price=2450.0,
            status="ACTIVE",
        )
        db.add(lot_101)

    lot_102 = db.query(Lot).filter(Lot.id == 102).first()
    if not lot_102:
        lot_102 = Lot(
            id=102,
            owner_type="FARMER",
            owner_id=1,
            commodity_id=2,
            variety="JS-335",
            quantity_quintals=45.0,
            quality_grade="FAQ",
            moisture_pct=11.8,
            storage_state="WAREHOUSE",
            location_address="Nagda Rural Warehouse, Ujjain, MP",
            location_lat=23.4510,
            location_lng=75.4210,
            harvest_date=date(2026, 3, 5),
            expected_selling_window_start=date(2026, 3, 10),
            expected_selling_window_end=date(2026, 4, 5),
            minimum_acceptable_price=4300.0,
            status="ACTIVE",
        )
        db.add(lot_102)

    master_lot_103 = db.query(Lot).filter(Lot.id == 103).first()
    if not master_lot_103:
        master_lot_103 = Lot(
            id=103,
            owner_type="FPO",
            owner_id=1,
            commodity_id=1,
            variety="Sharbati Premium",
            quantity_quintals=520.0,
            quality_grade="GRADE_A",
            moisture_pct=10.9,
            storage_state="WAREHOUSE",
            location_address="FPO Central Aggregation Hub, Ujjain, MP",
            location_lat=23.1765,
            location_lng=75.7885,
            harvest_date=date(2026, 3, 8),
            expected_selling_window_start=date(2026, 3, 12),
            expected_selling_window_end=date(2026, 4, 20),
            minimum_acceptable_price=2580.0,
            status="ACTIVE",
        )
        db.add(master_lot_103)
        db.flush()

        # Add Sub-Lot Contributions
        db.add(SubLotContribution(
            master_bulk_lot_id=103,
            child_lot_id=101,
            farmer_id=1,
            quantity_quintals=65.0,
            moisture_pct=11.2,
            quality_grade="GRADE_A",
            contribution_share_pct=12.5,
        ))

    # ------------------------------------------
    # H. 60-Day Historical Mandi Prices Time Series
    # ------------------------------------------
    existing_prices_count = db.query(MarketPrice).count()
    if existing_prices_count < 10:
        logger.info("Generating 60-day historical daily mandi price series...")
        today = date.today()
        price_records = []

        # Baseline modal prices: Wheat ~2540, Soybean ~4510
        for day_offset in range(60, -1, -1):
            curr_date = today - timedelta(days=day_offset)

            # 1. Ujjain Mandi - Wheat
            w_ujj = 2480.0 + (day_offset * -1.2) + ((day_offset % 7) * 4.5)
            price_records.append(MarketPrice(
                market_id=1, commodity_id=1, variety="Sharbati", arrival_date=curr_date,
                min_price=w_ujj - 65.0, max_price=w_ujj + 80.0, modal_price=w_ujj,
                arrivals_volume_tonnes=1200.0 + (day_offset * 5.0),
            ))

            # 2. Indore Mandi - Wheat
            w_ind = 2560.0 + (day_offset * -1.4) + ((day_offset % 5) * 5.0)
            price_records.append(MarketPrice(
                market_id=2, commodity_id=1, variety="Sharbati", arrival_date=curr_date,
                min_price=w_ind - 70.0, max_price=w_ind + 95.0, modal_price=w_ind,
                arrivals_volume_tonnes=1950.0 + (day_offset * 6.5),
            ))

            # 3. Ujjain Mandi - Soybean
            s_ujj = 4420.0 + (day_offset * 1.5) + ((day_offset % 6) * 8.0)
            price_records.append(MarketPrice(
                market_id=1, commodity_id=2, variety="JS-335", arrival_date=curr_date,
                min_price=s_ujj - 110.0, max_price=s_ujj + 130.0, modal_price=s_ujj,
                arrivals_volume_tonnes=1600.0 + (day_offset * 4.0),
            ))

        db.bulk_save_objects(price_records)

    # ------------------------------------------
    # I. Active Offer, Transaction, Logistics & Escrow
    # ------------------------------------------
    tx_exists = db.query(Transaction).filter(Transaction.id == 1).first()
    if not tx_exists:
        offer_1 = Offer(
            id=1,
            lot_id=101,
            requirement_id=1,
            buyer_id=1,
            seller_id=1,
            offered_price_per_quintal=2600.0,
            quantity_quintals=65.0,
            status="ACCEPTED",
            last_acted_by="BUYER",
            delivery_terms="EX_FARM",
            notes="Binding transaction created upon mutual agreement.",
        )
        db.add(offer_1)
        db.flush()

        tx_1 = Transaction(
            id=1,
            offer_id=1,
            agreed_price_per_quintal=2600.0,
            agreed_quantity_quintals=65.0,
            gross_revenue=169000.0,
            transport_cost=2100.0,
            storage_cost=650.0,
            handling_cost=500.0,
            net_realization=165750.0,
            status="ACCEPTED",
        )
        db.add(tx_1)
        db.flush()

        db.add(Logistics(
            id=1,
            transaction_id=1,
            vehicle_type="MEDIUM_TRUCK_5T",
            origin_address="Village Nagda, Ujjain, MP",
            destination_address="ITC Procurement Hub, Dewas Naka, Indore, MP",
            distance_km=58.5,
            estimated_cost=2100.0,
            driver_name="Balwant Singh",
            driver_phone="9826012345",
            vehicle_number="MP-13-GA-4589",
            status="BOOKED",
        ))

        db.add(Payment(
            id=1,
            transaction_id=1,
            amount=169000.0,
            payment_status="ESCROW_LOCKED",
            payment_method="ESCROW",
            reference_id="ESCROW-TXN-2026-99214",
            payer_id=3,
            payee_id=1,
            escrow_locked_at=datetime.now(timezone.utc),
        ))

    db.commit()
    logger.info("SIH 2026 Hackathon Demonstration Scenario seeded successfully!")


# ==========================================
# 3. Main Seeding Runner
# ==========================================
def seed_database():
    """
    Primary database setup & seeding entry point:
    1. Initializes table schemas via init_db().
    2. Runs Kaggle CSV ingestion if raw CSV files are present.
    3. Seeds complete SIH demonstration records.
    """
    logger.info("Starting database initialization and seeding...")
    init_db()
    with SessionLocal() as db:
        # 1. Seed full demonstration scenario first so core SIH IDs (1..4) are reserved
        seed_demonstration_scenario(db)

        # 2. Ingest Kaggle CSVs from data/raw/ (up to 10,000 records)
        ingested_count = ingest_kaggle_mandi_csv(db, raw_dir="data/raw", max_records=10000)
        logger.info(f"Ingested {ingested_count} records from Kaggle CSVs.")

    print("✓ KrishiDisha database initialized and seeded successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
