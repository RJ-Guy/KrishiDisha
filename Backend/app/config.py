"""
KrishiDisha — Central Application Configuration & Environment Settings.
Smart India Hackathon 2026 (Problem Statement ID 26132).
Autonomous Multi-Tier Backend API Engine.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

# Base directory paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseModel):
    """
    Centralized runtime environment settings for KrishiDisha.
    Supports environment variables with robust zero-configuration local fallbacks.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ------------------------------------------
    # 1. Application Metadata
    # ------------------------------------------
    app_name: str = Field(
        default_factory=lambda: os.getenv("APP_NAME", "KrishiDisha API Engine")
    )
    app_version: str = Field(
        default_factory=lambda: os.getenv("APP_VERSION", "1.0.0")
    )
    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    )
    api_v1_prefix: str = Field(
        default_factory=lambda: os.getenv("API_V1_PREFIX", "/api")
    )
    sih_problem_statement_id: str = "26132"
    team_name: str = "MakhanChor (IIIT Sri City)"

    # ------------------------------------------
    # 2. Host & Server Ports
    # ------------------------------------------
    host: str = Field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0")
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000"))
    )

    # ------------------------------------------
    # 3. Security & Authentication (JWT)
    # ------------------------------------------
    secret_key: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY",
            "krishidisha-sih2026-super-secure-production-secret-key-9812739",
        )
    )
    jwt_algorithm: str = Field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256")
    )
    access_token_expire_seconds: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days
    )
    password_salt: str = Field(
        default_factory=lambda: os.getenv("PASSWORD_SALT", "krishidisha_salt_2026")
    )

    # ------------------------------------------
    # 4. Database & Connection Pooling
    # ------------------------------------------
    database_url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./krishidisha.db")
    )
    postgres_default_url: str = "postgresql://postgres:postgres@localhost:5432/krishidisha"
    db_pool_size: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10"))
    )
    db_max_overflow: int = Field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True

    # ------------------------------------------
    # 5. CORS Middleware Whitelist
    # ------------------------------------------
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ]

    # ------------------------------------------
    # 6. Filesystem Paths
    # ------------------------------------------
    project_root_dir: str = str(PROJECT_ROOT)
    data_raw_dir: str = Field(
        default_factory=lambda: os.getenv("DATA_RAW_DIR", str(PROJECT_ROOT / "data" / "raw"))
    )
    data_processed_dir: str = Field(
        default_factory=lambda: os.getenv("DATA_PROCESSED_DIR", str(PROJECT_ROOT / "data" / "processed"))
    )
    model_artifacts_dir: str = Field(
        default_factory=lambda: os.getenv("MODEL_ARTIFACTS_DIR", str(BACKEND_DIR / "ml" / "model_artifacts"))
    )

    # ------------------------------------------
    # 7. Logistics & OSRM Engine Calibration
    # ------------------------------------------
    road_winding_factor: float = 1.28  # Haversine rural winding factor for India
    earth_radius_km: float = 6371.0
    osrm_base_url: str = Field(
        default_factory=lambda: os.getenv("OSRM_BASE_URL", "http://router.project-osrm.org/route/v1/driving")
    )

    # ------------------------------------------
    # 8. SIH Agricultural & Economic Benchmarks
    # ------------------------------------------
    default_mandi_cess_pct: float = 0.015  # 1.5% APMC market statutory cess
    default_handling_cost_per_q: float = 12.0  # ₹12/Quintal handling & bagging
    default_storage_monthly_per_q: float = 35.0  # ₹35/Quintal/Month WDRA certified warehouse
    default_storage_daily_per_q: float = 1.17  # ₹35 / 30 days
    default_base_freight_fare: float = 16.0  # ₹16/km base road freight
    default_freight_per_km_q: float = 0.38  # ₹0.38/km/Quintal variable freight
    default_min_freight_charge: float = 350.0  # ₹350 minimum freight charge
    default_max_moisture_pct: float = 12.0  # 12.0% statutory moisture threshold

    # ------------------------------------------
    # 9. Government Minimum Support Prices (MSP 2025-26)
    # ------------------------------------------
    msp_benchmarks: Dict[str, float] = {
        "wheat": 2275.0,
        "soybean": 4892.0,
        "gram": 5440.0,
        "mustard": 5650.0,
    }

    # Helper properties
    @property
    def is_sqlite(self) -> bool:
        """Returns True if the active database is SQLite."""
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """Returns True if the active database is PostgreSQL."""
        return self.database_url.startswith("postgresql")

    def get_public_config(self) -> Dict[str, Any]:
        """
        Returns a sanitized configuration dictionary safe for public API exposure
        (omits cryptographic secrets, database credentials, and internal salt).
        """
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "debug": self.debug,
            "api_v1_prefix": self.api_v1_prefix,
            "sih_problem_statement_id": self.sih_problem_statement_id,
            "team_name": self.team_name,
            "database_type": "sqlite" if self.is_sqlite else "postgresql",
            "cors_origins": self.cors_origins,
            "benchmarks": {
                "mandi_cess_pct": self.default_mandi_cess_pct,
                "handling_cost_per_q": self.default_handling_cost_per_q,
                "storage_monthly_per_q": self.default_storage_monthly_per_q,
                "max_moisture_pct": self.default_max_moisture_pct,
                "msp": self.msp_benchmarks,
            },
        }


# ==========================================
# Public Configuration Schema for API Handshake
# ==========================================
class AppConfigResponse(BaseModel):
    """Pydantic response schema for exposing public configuration to frontend."""
    app_name: str
    app_version: str
    environment: str
    debug: bool
    api_v1_prefix: str
    sih_problem_statement_id: str
    team_name: str
    database_type: str
    cors_origins: List[str]
    benchmarks: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# Singleton Settings Instance
settings = Settings()
