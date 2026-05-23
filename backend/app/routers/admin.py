from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import crud
from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole
from app.schemas import SystemLogResponse, SystemSettingsUpdate
from app.services.audit import log_event

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/logs", response_model=list[SystemLogResponse])
def list_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    return crud.list_system_logs(db, limit)


@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    return crud.get_system_settings(db)


@router.put("/settings")
def update_settings(
    body: SystemSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    values = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    result = crud.update_system_settings(db, values)
    log_event(
        db,
        action="settings.update",
        message=f"Updated settings: {', '.join(values.keys())}",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        extra=values,
    )
    return result
