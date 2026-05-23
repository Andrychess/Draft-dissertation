from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole
from app.schemas import GroupCreate, GroupResponse

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("", response_model=list[GroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.teacher)),
):
    return crud.list_groups(db)


@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    from app.models import StudyGroup

    if db.query(StudyGroup).filter(StudyGroup.cipher == body.cipher).first():
        raise HTTPException(status_code=400, detail="Group already exists")
    return crud.create_group(db, body.cipher, body.name)
