"""FastAPI application entry point for the lab provisioning portal."""

from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db

app = FastAPI(
    title="Lab Provisioning Portal",
    description="Automated containerized lab provisioning backend API.",
    version="0.1.0",
)


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Verify API and database connectivity.

    Args:
        db: Injected SQLAlchemy session from ``get_db``.

    Returns:
        dict[str, Any]: Health payload with API status and database state.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except SQLAlchemyError:
        db_status = "disconnected"

    return {"status": "ok", "db": db_status}
