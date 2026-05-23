import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud
from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole, Verdict
from app.schemas import (
    AICheckResultResponse,
    ResultApprove,
    ResultCorrect,
    ResultDetailResponse,
    SessionResultRow,
)

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/sessions/{session_id}/results", response_model=list[SessionResultRow])
def session_results(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    return crud.get_session_results(db, session_id)


@router.get("/results/{sheet_id}", response_model=list[ResultDetailResponse])
def result_details(
    sheet_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    rows = crud.get_sheet_rows(db, sheet_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Sheet not found")
    out = []
    for row in rows:
        ai = row.ai_results[0] if row.ai_results else None
        out.append(
            ResultDetailResponse(
                sheet_id=row.sheet_id,
                question_id=row.question_id,
                student_name=row.student_name,
                group_cipher=row.group_cipher,
                answer_text=row.student_answer.answer_text if row.student_answer else None,
                submitted_at=row.submitted_at,
                ai_result=AICheckResultResponse.model_validate(ai) if ai else None,
            )
        )
    return out


@router.put("/results/{check_id}/approve", response_model=AICheckResultResponse)
def approve_result(
    check_id: int,
    _: ResultApprove,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    result = crud.get_ai_result(db, check_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return crud.approve_result(db, result, user.id)


@router.put("/results/{check_id}", response_model=AICheckResultResponse)
def correct_result(
    check_id: int,
    body: ResultCorrect,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    result = crud.get_ai_result(db, check_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    try:
        return crud.correct_result(db, result, body.corrected_score, body.explanation)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    results = crud.get_session_results(db, session_id)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["sheet_id", "student_name", "group_cipher", "total_score", "max_score", "verdict"],
    )
    writer.writeheader()
    writer.writerows(results)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}_results.csv"},
    )
