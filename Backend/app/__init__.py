"""
KrishiDisha — Core Backend Application Package.
Smart India Hackathon 2026 (Problem Statement ID 26132).
Autonomous Multi-Tier Backend API Engine.
"""

from app.config import (
    Settings,
    settings,
    AppConfigResponse,
    PROJECT_ROOT,
    BACKEND_DIR,
)

__version__ = "1.0.0"
__author__ = "Team MakhanChor (IIIT Sri City)"
__sih_problem_id__ = "26132"

__all__ = [
    "Settings",
    "settings",
    "AppConfigResponse",
    "PROJECT_ROOT",
    "BACKEND_DIR",
    "__version__",
    "__author__",
    "__sih_problem_id__",
]
