import logging
import sys
from logging.config import dictConfig


def setup_logging(debug: bool = False) -> None:
    """
    Configure application-wide logging.

    - Logs to stdout (Docker-friendly)
    - Uses structured, readable log format
    - Avoids logging sensitive data
    - Debug flag controls log level
    """

    log_level = "DEBUG" if debug else "INFO"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s | %(levelname)s | "
                    "%(name)s | %(message)s"
                )
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": sys.stdout,
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["default"],
        },
    }

    dictConfig(logging_config)
