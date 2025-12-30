"""
SQLAlchemy base class for all ORM models.

All database models should inherit from Base.
This allows SQLAlchemy to discover tables and metadata
in one central place.
"""

from sqlalchemy.orm import declarative_base

# Base class for all ORM models
Base = declarative_base()
