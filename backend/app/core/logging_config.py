import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure application-wide logging.

    This function should be called once when the FastAPI application starts.
    """

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(filename)s:%(lineno)d | %(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )