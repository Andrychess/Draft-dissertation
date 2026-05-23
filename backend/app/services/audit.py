from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import SystemLog


def log_event(
    db: Session,
    action: str,
    message: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> SystemLog:
    entry = SystemLog(
        action=action,
        message=message,
        user_id=user_id,
        ip_address=ip_address,
        extra=extra,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
