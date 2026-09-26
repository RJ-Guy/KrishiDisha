"""
Authentication, User Registration, and Profile Management Router for KrishiDisha.
Supports role-based access control (FARMER, FPO, BUYER, ADMIN),
profile entity creation, and secure JWT session management.
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

# Schemas
from app.schemas.auth_schema import (
    UserRole,
    LanguagePreference,
    Token,
    TokenPayload,
    RefreshTokenRequest,
    UserLogin,
    FarmerProfileCreate,
    FarmerProfileResponse,
    FPOProfileCreate,
    FPOProfileResponse,
    BuyerProfileCreate,
    BuyerProfileResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
)

# Models
try:
    from app.models.user import User, Farmer, FPO
    from app.models.buyer import Buyer
except ImportError:
    User = Farmer = FPO = Buyer = None

# Database Session Dependency
try:
    from app.database.connection import get_db as _app_get_db
except (ImportError, AttributeError):
    _app_get_db = None


def get_db() -> Generator[Optional[Session], None, None]:
    """Yield a database session if available, otherwise None."""
    if _app_get_db is not None:
        yield from _app_get_db()
    else:
        yield None


# ==========================================
# Secret Key & Cryptographic Helpers
# ==========================================
JWT_SECRET = "krishidisha-sih2026-super-secure-production-secret-key-9812739"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Deterministic salted SHA-256 hash for portable authentication."""
    salt = "krishidisha_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hash_password(plain_password) == hashed_password


def create_access_token(user_id: int, role: str, phone: str) -> str:
    """Generate signed JWT-compatible base64url token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "phone": phone,
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
    }

    hdr_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    pay_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{hdr_b64}.{pay_b64}"
    sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")

    return f"{signing_input}.{sig_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode signed token payload."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token structure")
        signing_input = f"{parts[0]}.{parts[1]}"
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(parts[2] + "==")
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Signature mismatch")

        payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_bytes.decode())

        if payload.get("exp") and payload["exp"] < time.time():
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==========================================
# In-Memory Mock Store (Fallback when DB offline)
# ==========================================
_MOCK_USERS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "email": "ramesh.farmer@krishidisha.in",
        "phone": "9876543210",
        "password_hash": hash_password("farmer123"),
        "full_name": "Ramesh Chandra Patel",
        "role": UserRole.FARMER,
        "language_preference": LanguagePreference.HI,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "farmer_profile": {
            "id": 1,
            "user_id": 1,
            "state": "Madhya Pradesh",
            "district": "Ujjain",
            "village": "Nagda",
            "pin_code": "456335",
            "land_size_acres": 4.5,
            "primary_crops": ["Wheat", "Soybean", "Gram"],
            "fpo_id": 1,
            "created_at": datetime.now(timezone.utc),
        },
        "fpo_profile": None,
        "buyer_profile": None,
    },
    2: {
        "id": 2,
        "email": "ujjain.kisan.fpo@krishidisha.in",
        "phone": "9876543211",
        "password_hash": hash_password("fpo12345"),
        "full_name": "Ujjain Kisan Samriddhi FPO",
        "role": UserRole.FPO,
        "language_preference": LanguagePreference.HI,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "farmer_profile": None,
        "fpo_profile": {
            "id": 1,
            "user_id": 2,
            "organization_name": "Ujjain Kisan Samriddhi Agro Producer Co.",
            "registration_no": "FPO-MP-UJJ-2024-0089",
            "state": "Madhya Pradesh",
            "district": "Ujjain",
            "member_count": 480,
            "storage_capacity_quintals": 12500.0,
            "created_at": datetime.now(timezone.utc),
        },
        "buyer_profile": None,
    },
    3: {
        "id": 3,
        "email": "procurement@itc-agri.com",
        "phone": "9876543212",
        "password_hash": hash_password("buyer123"),
        "full_name": "ITC Agri Business Division",
        "role": UserRole.BUYER,
        "language_preference": LanguagePreference.EN,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "farmer_profile": None,
        "fpo_profile": None,
        "buyer_profile": {
            "id": 1,
            "user_id": 3,
            "company_name": "ITC Limited Agri Business",
            "gst_no": "23AAACI1681G1Z0",
            "trade_license": "TL-MP-IND-88219",
            "buyer_category": "INSTITUTIONAL",
            "reliability_score": 98.5,
            "verified": True,
            "operating_states": ["Madhya Pradesh", "Rajasthan", "Maharashtra"],
            "created_at": datetime.now(timezone.utc),
        },
    },
}


# ==========================================
# Authentication & Role Dependencies
# ==========================================
def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Optional[Session] = Depends(get_db),
) -> Dict[str, Any]:
    """
    Extracts Bearer token from header, validates payload,
    and returns user dictionary or ORM instance.
    """
    if not authorization:
        # Default mock user for testing if no token provided
        return _MOCK_USERS[1]

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
        )

    payload = decode_access_token(parts[1])
    user_id = int(payload.get("sub", 0))

    if db is not None and User is not None:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            return user

    if user_id in _MOCK_USERS:
        return _MOCK_USERS[user_id]

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")


def require_role(*allowed_roles: UserRole):
    """Dependency factory ensuring authenticated user belongs to allowed roles."""
    def role_checker(current_user: Any = Depends(get_current_user)):
        user_role = getattr(current_user, "role", None) or current_user.get("role")
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role)
            except ValueError:
                pass
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action restricted to roles: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


# ==========================================
# Router Definition
# ==========================================
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register User")
def register_user(payload: UserCreate, db: Optional[Session] = Depends(get_db)):
    """
    Register a new user account with role-specific profile (FARMER, FPO, BUYER, ADMIN).
    """
    # Check for existing email/phone
    if db is not None and User is not None:
        if payload.email and db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        if db.query(User).filter(User.phone == payload.phone).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")

        new_user = User(
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role.value,
            language_preference=payload.language_preference.value,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        # Add profile
        if payload.role == UserRole.FARMER and payload.farmer_profile and Farmer is not None:
            farmer = Farmer(
                user_id=new_user.id,
                state=payload.farmer_profile.state,
                district=payload.farmer_profile.district,
                village=payload.farmer_profile.village,
                pin_code=payload.farmer_profile.pin_code,
                land_size_acres=payload.farmer_profile.land_size_acres,
                primary_crops=payload.farmer_profile.primary_crops,
                fpo_id=payload.farmer_profile.fpo_id,
            )
            db.add(farmer)
        elif payload.role == UserRole.FPO and payload.fpo_profile and FPO is not None:
            fpo = FPO(
                user_id=new_user.id,
                organization_name=payload.fpo_profile.organization_name,
                registration_no=payload.fpo_profile.registration_no,
                state=payload.fpo_profile.state,
                district=payload.fpo_profile.district,
                member_count=payload.fpo_profile.member_count or 0,
                storage_capacity_quintals=payload.fpo_profile.storage_capacity_quintals or 0.0,
            )
            db.add(fpo)
        elif payload.role == UserRole.BUYER and payload.buyer_profile and Buyer is not None:
            buyer = Buyer(
                user_id=new_user.id,
                company_name=payload.buyer_profile.company_name,
                gst_no=payload.buyer_profile.gst_no,
                trade_license=payload.buyer_profile.trade_license,
                buyer_category=payload.buyer_profile.buyer_category or "INSTITUTIONAL",
                operating_states=payload.buyer_profile.operating_states,
            )
            db.add(buyer)

        db.commit()
        db.refresh(new_user)
        return new_user

    # In-memory mock registration
    new_id = max(_MOCK_USERS.keys(), default=0) + 1
    user_record = {
        "id": new_id,
        "email": payload.email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "role": payload.role,
        "language_preference": payload.language_preference,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "farmer_profile": None,
        "fpo_profile": None,
        "buyer_profile": None,
    }

    if payload.role == UserRole.FARMER and payload.farmer_profile:
        user_record["farmer_profile"] = {
            "id": new_id,
            "user_id": new_id,
            **payload.farmer_profile.model_dump(),
            "created_at": datetime.now(timezone.utc),
        }
    elif payload.role == UserRole.FPO and payload.fpo_profile:
        user_record["fpo_profile"] = {
            "id": new_id,
            "user_id": new_id,
            **payload.fpo_profile.model_dump(),
            "created_at": datetime.now(timezone.utc),
        }
    elif payload.role == UserRole.BUYER and payload.buyer_profile:
        user_record["buyer_profile"] = {
            "id": new_id,
            "user_id": new_id,
            **payload.buyer_profile.model_dump(),
            "reliability_score": 100.0,
            "verified": False,
            "created_at": datetime.now(timezone.utc),
        }

    _MOCK_USERS[new_id] = user_record
    return user_record


@router.post("/login", response_model=Token, summary="Authenticate and Receive Token")
def login_user(payload: UserLogin, db: Optional[Session] = Depends(get_db)):
    """
    Authenticate user by email or phone and password, returning JWT access token.
    """
    if db is not None and User is not None:
        user = db.query(User).filter(
            (User.email == payload.email_or_phone) | (User.phone == payload.email_or_phone)
        ).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone/email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
        token_str = create_access_token(user.id, user.role, user.phone)
        return Token(access_token=token_str, token_type="bearer", role=UserRole(user.role), user_id=user.id)

    # In-memory lookup
    for u in _MOCK_USERS.values():
        if (u.get("email") == payload.email_or_phone or u.get("phone") == payload.email_or_phone) and verify_password(payload.password, u["password_hash"]):
            token_str = create_access_token(u["id"], u["role"].value if hasattr(u["role"], "value") else str(u["role"]), u["phone"])
            return Token(
                access_token=token_str,
                token_type="bearer",
                role=u["role"] if isinstance(u["role"], UserRole) else UserRole(u["role"]),
                user_id=u["id"],
            )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone/email or password")


@router.post("/refresh", response_model=Token, summary="Refresh Access Token")
def refresh_token(payload: RefreshTokenRequest):
    """Validate refresh token and issue a fresh access token."""
    decoded = decode_access_token(payload.refresh_token)
    user_id = int(decoded.get("sub", 0))
    role_str = decoded.get("role", UserRole.FARMER.value)
    phone_str = decoded.get("phone", "")
    new_token = create_access_token(user_id, role_str, phone_str)
    return Token(access_token=new_token, token_type="bearer", role=UserRole(role_str), user_id=user_id)


@router.get("/me", response_model=UserResponse, summary="Get Current Profile")
def get_current_profile(current_user: Any = Depends(get_current_user)):
    """Retrieve authenticated user's account details and linked profile."""
    return current_user


@router.put("/profile", response_model=UserResponse, summary="Update Current Profile")
def update_profile(
    payload: UserUpdate,
    current_user: Any = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """Update profile attributes for currently logged in user."""
    if db is not None and isinstance(current_user, User):
        if payload.email is not None:
            current_user.email = payload.email
        if payload.phone is not None:
            current_user.phone = payload.phone
        if payload.full_name is not None:
            current_user.full_name = payload.full_name
        if payload.language_preference is not None:
            current_user.language_preference = payload.language_preference.value
        db.commit()
        db.refresh(current_user)
        return current_user

    # Mock in-memory update
    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    if user_id in _MOCK_USERS:
        u = _MOCK_USERS[user_id]
        if payload.email is not None:
            u["email"] = payload.email
        if payload.phone is not None:
            u["phone"] = payload.phone
        if payload.full_name is not None:
            u["full_name"] = payload.full_name
        if payload.language_preference is not None:
            u["language_preference"] = payload.language_preference
        return u

    return current_user
