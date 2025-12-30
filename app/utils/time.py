# app/utils/time.py
"""
Time utilities for handling timezone-aware and timezone-naive datetimes.

This module provides utilities to work with both PostgreSQL (timezone-aware)
and SQLite (timezone-naive) databases.
"""

from datetime import datetime, timezone
import os


def now_utc() -> datetime:
    """
    Get current UTC time.

    Returns timezone-aware datetime for PostgreSQL,
    timezone-naive datetime for SQLite (testing).
    """
    if os.getenv("TESTING") == "true":
        # SQLite: Return timezone-naive UTC datetime
        return datetime.utcnow()
    else:
        # PostgreSQL: Return timezone-aware UTC datetime
        return datetime.now(timezone.utc)


def make_comparable(dt: datetime) -> datetime:
    """
    Make a datetime comparable with current environment.

    In testing (SQLite): Removes timezone info
    In production (PostgreSQL): Ensures timezone info

    Args:
        dt: Datetime to make comparable

    Returns:
        Datetime that can be compared with now_utc()
    """
    if dt is None:
        return None

    if os.getenv("TESTING") == "true":
        # SQLite: Remove timezone info
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    else:
        # PostgreSQL: Ensure timezone info
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt