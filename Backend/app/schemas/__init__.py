"""
KrishiDisha Schemas Registry.
Exports all Pydantic models, request/response DTOs, and validation enums
for seamless import across FastAPI routes, services, and tests.
"""

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

from app.schemas.lot_schema import (
    OwnerType,
    LotStatus,
    QualityGrade,
    StorageState,
    QualityMetrics,
    LotBase,
    LotCreate,
    LotUpdate,
    LotResponse,
    SubLotContribution,
    BulkLotCreate,
    AggregatedLotResponse,
    LotFilterParams,
)

from app.schemas.market_schema import (
    PriceTrend,
    MandiBase,
    MandiCreate,
    MandiResponse,
    MarketPriceCreate,
    MarketPriceResponse,
    MandiPriceFilter,
    PriceTrendPoint,
    HistoricalPriceQuery,
    MarketTrendsResponse,
    ProcurementOptionCreate,
    ProcurementOptionResponse,
)

from app.schemas.buyer_schema import (
    BuyerCategory,
    RequirementStatus,
    BuyerResponse,
    BuyerRequirementBase,
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
    BuyerRequirementResponse,
    BuyerMatchScoreBreakdown,
    BuyerMatchResult,
    BuyerMatchQuery,
)

from app.schemas.transaction_schema import (
    OfferStatus,
    TransactionStatus,
    OfferInitiator,
    OfferCreate,
    CounterOfferRequest,
    OfferResponse,
    QualityInspectionSlip,
    TransactionCreate,
    TransactionStateUpdate,
    TransactionResponse,
)

from app.schemas.forecast_schema import (
    ForecastTrend,
    DailyForecastPoint,
    ForecastRequest,
    ForecastResponse,
)

from app.schemas.logistics_schema import (
    VehicleType,
    LogisticsStatus,
    VehicleClassDetail,
    LogisticsQuoteRequest,
    LogisticsQuoteResponse,
    LogisticsBookingCreate,
    LogisticsResponse,
)

from app.schemas.payment_schema import (
    PaymentStatus,
    PaymentMethod,
    SmallholderPayout,
    PaymentCreate,
    PaymentStatusUpdate,
    EscrowStatusResponse,
    PaymentResponse,
)

from app.schemas.grievance_schema import (
    GrievanceCategory,
    GrievanceStatus,
    GrievanceCreate,
    GrievanceResolution,
    GrievanceResponse,
)

from app.schemas.report_schema import (
    DecisionVerdict,
    SellingChannel,
    LiquidityUrgency,
    NetRealizationItem,
    MSPComparisonItem,
    DecisionRequest,
    DecisionRecommendationResponse,
    VarianceItem,
    RealizationVarianceReport,
)

__all__ = [
    # Auth
    "UserRole",
    "LanguagePreference",
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    "UserLogin",
    "FarmerProfileCreate",
    "FarmerProfileResponse",
    "FPOProfileCreate",
    "FPOProfileResponse",
    "BuyerProfileCreate",
    "BuyerProfileResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Lots
    "OwnerType",
    "LotStatus",
    "QualityGrade",
    "StorageState",
    "QualityMetrics",
    "LotBase",
    "LotCreate",
    "LotUpdate",
    "LotResponse",
    "SubLotContribution",
    "BulkLotCreate",
    "AggregatedLotResponse",
    "LotFilterParams",
    # Market
    "PriceTrend",
    "MandiBase",
    "MandiCreate",
    "MandiResponse",
    "MarketPriceCreate",
    "MarketPriceResponse",
    "MandiPriceFilter",
    "PriceTrendPoint",
    "HistoricalPriceQuery",
    "MarketTrendsResponse",
    "ProcurementOptionCreate",
    "ProcurementOptionResponse",
    # Buyer
    "BuyerCategory",
    "RequirementStatus",
    "BuyerResponse",
    "BuyerRequirementBase",
    "BuyerRequirementCreate",
    "BuyerRequirementUpdate",
    "BuyerRequirementResponse",
    "BuyerMatchScoreBreakdown",
    "BuyerMatchResult",
    "BuyerMatchQuery",
    # Transactions
    "OfferStatus",
    "TransactionStatus",
    "OfferInitiator",
    "OfferCreate",
    "CounterOfferRequest",
    "OfferResponse",
    "QualityInspectionSlip",
    "TransactionCreate",
    "TransactionStateUpdate",
    "TransactionResponse",
    # Forecast
    "ForecastTrend",
    "DailyForecastPoint",
    "ForecastRequest",
    "ForecastResponse",
    # Logistics
    "VehicleType",
    "LogisticsStatus",
    "VehicleClassDetail",
    "LogisticsQuoteRequest",
    "LogisticsQuoteResponse",
    "LogisticsBookingCreate",
    "LogisticsResponse",
    # Payment
    "PaymentStatus",
    "PaymentMethod",
    "SmallholderPayout",
    "PaymentCreate",
    "PaymentStatusUpdate",
    "EscrowStatusResponse",
    "PaymentResponse",
    # Grievance
    "GrievanceCategory",
    "GrievanceStatus",
    "GrievanceCreate",
    "GrievanceResolution",
    "GrievanceResponse",
    # Report / Decision
    "DecisionVerdict",
    "SellingChannel",
    "LiquidityUrgency",
    "NetRealizationItem",
    "MSPComparisonItem",
    "DecisionRequest",
    "DecisionRecommendationResponse",
    "VarianceItem",
    "RealizationVarianceReport",
]
