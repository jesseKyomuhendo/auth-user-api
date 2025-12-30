# app/main.py
"""
FastAPI application entry point.

This module initializes the FastAPI application, sets up middleware,
includes routers, and handles startup/shutdown events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine

# Setup application logging
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables on startup
# Note: In production, use Alembic migrations instead
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    raise

# Initialize FastAPI application
app = FastAPI(
    title="Auth & User Management API",
    description="""
    Authentication and User Management API for a SaaS Platform

    ## Features
    * JWT-based authentication (access + refresh tokens)
    * Role-based access control (RBAC)
    * User registration and profile management
    * Admin user management endpoints
    * Secure password hashing
    * Refresh token rotation

    ## Authentication
    Most endpoints require authentication via Bearer token in the Authorization header:
```
    Authorization: Bearer <your_access_token>
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
# In production, replace "*" with specific allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with version prefix
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint - basic health check.

    Returns service name and status.
    """
    return {
        "service": settings.APP_NAME,
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Detailed health check endpoint.

    Checks:
    - API service status
    - Database connectivity (basic)

    In production, this should include:
    - Database connection pool status
    - Cache connectivity (if applicable)
    - External service dependencies
    """
    health_status = {
        "status": "healthy",
        "api": "operational",
        "database": "connected",  # Could add actual DB ping here
    }

    return health_status


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Executes when the application starts.
    Can be used for:
    - Database connection verification
    - Cache warmup
    - External service health checks
    """
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # ✅ ADD THIS SECTION:
    logger.info("=" * 70)
    logger.info(" API Server Started Successfully!")
    logger.info("=" * 70)
    logger.info(" Access the API at:")
    logger.info("   • API:      http://localhost:8000")
    logger.info("   • Docs:     http://localhost:8000/docs")
    logger.info("   • ReDoc:    http://localhost:8000/redoc")
    logger.info("   • Health:   http://localhost:8000/health")
    logger.info("   • OpenAPI:  http://localhost:8000/openapi.json")
    logger.info("=" * 70)

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.

    Executes when the application shuts down.
    Can be used for:
    - Closing database connections
    - Cleanup tasks
    - Logging shutdown events
    """
    logger.info(f"Shutting down {settings.APP_NAME}")
    logger.info("Application shutdown complete")