"""
Authentication, User, and Profile Pydantic Schemas for KrishiDisha.
Supports role-based access (FARMER, FPO, BUYER, ADMIN) and profile entities.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    FARMER = "FARMER"
    FPO = "FPO"
    BUYER = "BUYER"
    ADMIN = "ADMIN"


class LanguagePreference(str, Enum):
    EN = "en"
    HI = "hi"
    TE = "te"
    TA = "ta"
    MR = "mr"
    PA = "pa"


# ==========================================
# Token & Authentication Schemas
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[UserRole] = None
    exp: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserLogin(BaseModel):
    email_or_phone: str = Field(..., description="Email or 10-digit mobile number")
    password: str = Field(..., min_length=6, description="User password")


# ==========================================
# Profile Schemas
# ==========================================

class FarmerProfileCreate(BaseModel):
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    village: Optional[str] = Field(default=None, max_length=100)
    pin_code: Optional[str] = Field(default=None, max_length=10)
    land_size_acres: Optional[float] = Field(default=None, ge=0.0)
    primary_crops: Optional[List[str]] = Field(default_factory=list)
    fpo_id: Optional[int] = None


class FarmerProfileResponse(BaseModel):
    id: int
    user_id: int
    state: str
    district: str
    village: Optional[str] = None
    pin_code: Optional[str] = None
    land_size_acres: Optional[float] = None
    primary_crops: Optional[List[str]] = None
    fpo_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FPOProfileCreate(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=200)
    registration_no: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    member_count: Optional[int] = Field(default=0, ge=0)
    storage_capacity_quintals: Optional[float] = Field(default=0.0, ge=0.0)


class FPOProfileResponse(BaseModel):
    id: int
    user_id: int
    organization_name: str
    registration_no: str
    state: str
    district: str
    member_count: int = 0
    storage_capacity_quintals: float = 0.0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BuyerProfileCreate(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=200)
    gst_no: Optional[str] = Field(default=None, max_length=50)
    trade_license: Optional[str] = Field(default=None, max_length=100)
    buyer_category: Optional[str] = Field(default="INSTITUTIONAL", description="INSTITUTIONAL, PROCESSOR, EXPORTER, LOCAL_TRADER")
    operating_states: Optional[List[str]] = Field(default_factory=list)


class BuyerProfileResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    gst_no: Optional[str] = None
    trade_license: Optional[str] = None
    buyer_category: Optional[str] = "INSTITUTIONAL"
    reliability_score: float = Field(default=100.0, ge=0.0, le=100.0)
    verified: bool = False
    operating_states: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# User Account Schemas
# ==========================================

class UserCreate(BaseModel):
    email: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="User email address")
    phone: str = Field(..., min_length=10, max_length=15, description="Mobile number with country or national format")
    password: str = Field(..., min_length=6, description="Password min length 6")
    full_name: str = Field(..., min_length=2, max_length=150)
    role: UserRole
    language_preference: LanguagePreference = LanguagePreference.HI

    farmer_profile: Optional[FarmerProfileCreate] = None
    fpo_profile: Optional[FPOProfileCreate] = None
    buyer_profile: Optional[BuyerProfileCreate] = None


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone: Optional[str] = Field(default=None, min_length=10, max_length=15)
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    language_preference: Optional[LanguagePreference] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    phone: str
    full_name: str
    role: UserRole
    language_preference: LanguagePreference
    is_active: bool = True
    created_at: datetime

    farmer_profile: Optional[FarmerProfileResponse] = None
    fpo_profile: Optional[FPOProfileResponse] = None
    buyer_profile: Optional[BuyerProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
