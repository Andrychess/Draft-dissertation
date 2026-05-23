from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole
from app.schemas import QuestionResponse, QuestionUpdate

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.put("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    question = crud.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return crud.update_question(db, question, **body.model_dump(exclude_unset=True))


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    question = crud.get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    crud.delete_question(db, question)
