from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models import SessionStatus, User, UserRole
from app.schemas import (
    QuestionResponse,
    SessionCreate,
    SessionExtend,
    SessionJoinRequest,
    SessionJoinResponse,
    SessionResponse,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    if user.role == UserRole.admin:
        return crud.list_sessions(db)
    return crud.list_sessions(db, user_id=user.id)


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    return crud.create_session(
        db,
        body.name,
        body.template_id,
        user.id,
        body.group_ciphers,
        body.start_time,
        body.end_time,
    )


@router.put("/{session_id}/extend", response_model=SessionResponse)
def extend_session(
    session_id: int,
    body: SessionExtend,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return crud.extend_session(db, session, body.end_time)


@router.post("/{session_id}/finish", response_model=SessionResponse)
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return crud.finish_session(db, session)


@router.get("/join/{code}", response_model=SessionResponse)
def check_join_code(code: str, db: Session = Depends(get_db)):
    session = crud.get_session_by_code(db, code)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid connection code")
    if session.status == SessionStatus.finished:
        raise HTTPException(status_code=400, detail="Session is finished")
    return session


@router.post("/join", response_model=SessionJoinResponse)
def join_session(body: SessionJoinRequest, db: Session = Depends(get_db)):
    session = crud.get_session_by_code(db, body.connection_code)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid connection code")
    if session.status == SessionStatus.finished:
        raise HTTPException(status_code=400, detail="Session is finished")
    if not body.student_name and not (body.last_name and body.first_name):
        raise HTTPException(status_code=400, detail="Provide student_name or last_name + first_name")
    try:
        session_id, sheet_id = crud.join_session(
            db,
            session,
            body.student_name,
            body.group_cipher,
            body.last_name,
            body.first_name,
            body.patronymic,
            body.device_fingerprint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session = crud.get_session(db, session_id)
    return SessionJoinResponse(
        session_id=session_id,
        sheet_id=sheet_id,
        session_name=session.name if session else "",
        status=session.status if session else SessionStatus.active,
    )


@router.get("/{session_id}/questions", response_model=list[QuestionResponse])
def session_questions(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == SessionStatus.finished:
        raise HTTPException(status_code=400, detail="Session is finished")
    return session.template.questions
