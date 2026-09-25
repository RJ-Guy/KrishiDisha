"""
KrishiDisha — Main FastAPI Application Entry Point.
Smart India Hackathon 2026 (Problem Statement ID 26132).
Autonomous Multi-Tier Backend API Engine.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import init_db, check_connection, SessionLocal
from app.database.seed_data import seed_database
from app.routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("krishidisha.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    logger.info("Starting KrishiDisha Backend Engine...")
    try:
        init_db()
        is_connected = check_connection()
        logger.info(f"Database connection verified: {'HEALTHY' if is_connected else 'UNREACHABLE'}")

        # Auto-seed check: if tables are empty, auto-populate demonstration and Kaggle dataset
        try:
            with SessionLocal() as db:
                from app.models.market import Market
                if db.query(Market).count() == 0:
                    logger.info("Fresh database detected. Auto-running initial data seed...")
                    seed_database()
                    logger.info("Automatic startup seeding completed.")
        except Exception as seed_err:
            logger.warning(f"Startup auto-seed check skipped or failed non-fatally: {seed_err}")

    except Exception as e:
        logger.error(f"Error during startup database initialization: {e}")
    yield
    logger.info("Shutting down KrishiDisha Backend Engine...")


app = FastAPI(
    title="KrishiDisha API Engine",
    description=(
        "Comprehensive backend services and quantitative decision intelligence platform "
        "for agricultural smallholders, FPOs, institutional buyers, and APMC mandis. "
        "Smart India Hackathon 2026 — Problem Statement ID 26132."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for Uncaught Server Errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Uniform error response for uncaught server-side exceptions."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred while processing your request.",
            "error_type": exc.__class__.__name__,
            "path": str(request.url.path),
        },
    )


# Mount Unified API Router (/api)
app.include_router(api_router)


@app.get("/", tags=["Root"], summary="KrishiDisha Service Information")
def root():
    """Root health and discovery endpoint."""
    return {
        "service": "KrishiDisha Central API Engine",
        "version": "1.0.0",
        "status": "online",
        "sih_problem_statement": "26132",
        "documentation": "/docs",
        "endpoints_prefix": "/api",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
