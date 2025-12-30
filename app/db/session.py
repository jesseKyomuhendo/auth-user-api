"""
Database session setup.

This module is responsible for:
- Creating the SQLAlchemy engine
- Providing a session factory
- Supplying a DB session dependency for FastAPI

All database access should go through sessions created here.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# =========================
# SQLAlchemy Engine
# =========================
# pool_pre_ping=True:
#   Ensures stale DB connections are detected and refreshed.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# =========================
# Session Factory
# =========================
# autocommit=False:
#   Transactions are committed explicitly.
# autoflush=False:
#   Prevents automatic flushes before queries.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# =========================
# FastAPI Dependency
# =========================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    - Opens a session per request
    - Automatically commits on success
    - Rolls back on exceptions
    - Ensures the session is always closed
    
    This pattern ensures data is persisted when requests complete successfully
    and rolled back when errors occur.
    """
    db = SessionLocal()
    try:
        yield db
        # Commit the transaction if no exception occurred
        db.commit()
    except Exception:
        # Rollback on any exception
        db.rollback()
        raise
    finally:
        # Always close the session
        db.close()
