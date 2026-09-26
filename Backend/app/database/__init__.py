"""
KrishiDisha Database Layer Package.
Exports Base, engine, SessionLocal, get_db, init_db, check_connection,
and seed_database for clean imports across application modules.
"""

from app.database.connection import (
    Base,
    engine,
    SessionLocal,
    get_db,
    init_db,
    check_connection,
)
from app.database.seed_data import (
    seed_database,
    ingest_kaggle_mandi_csv,
    seed_demonstration_scenario,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "check_connection",
    "seed_database",
    "ingest_kaggle_mandi_csv",
    "seed_demonstration_scenario",
]
