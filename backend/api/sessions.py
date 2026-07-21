"""Session management endpoints for lab provisioning."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.docker_utils import get_free_port, kill_container, spawn_container
from backend.database import get_db
from backend.models.models import ActiveSession, LabTemplate

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=dict[str, Any])
def create_session(
    payload: dict[str, int],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Create a new active lab session for a user and template.

    Args:
        payload: Request body containing ``template_id`` and ``user_id``.
        db: Database session dependency.

    Returns:
        dict[str, Any]: Newly created session payload including access URL.
    """
    template_id = payload.get("template_id")
    user_id = payload.get("user_id")
    if template_id is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="template_id and user_id are required",
        )

    template = db.query(LabTemplate).filter(LabTemplate.id == template_id).first()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab template not found",
        )

    port = get_free_port()
    container_id = spawn_container(
        image_tag=template.image_tag,
        cpu_limit=template.cpu_limit,
        ram_limit=template.ram_limit,
        port=port,
    )

    session = ActiveSession(
        user_id=user_id,
        template_id=template.id,
        container_id=container_id,
        port=port,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "template_id": session.template_id,
        "container_id": session.container_id,
        "port": session.port,
        "status": session.status,
        "access_url": f"http://localhost:{session.port}",
    }


@router.delete("/{session_id}", response_model=dict[str, str])
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Stop and remove an active lab session.

    Args:
        session_id: Identifier of the session to delete.
        db: Database session dependency.

    Returns:
        dict[str, str]: A success message.
    """
    session = (
        db.query(ActiveSession)
        .filter(ActiveSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    kill_container(session.container_id)
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}
