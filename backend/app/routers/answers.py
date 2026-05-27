import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import get_db
from app.schemas import AnswerSaveRequest, AnswerSaveResponse, AnswerSubmitRequest
from app.services.ai_client import AIClient
from app.services.orchestrator import Orchestrator

router = APIRouter(prefix="/api/answers", tags=["answers"])


async def _run_orchestrator(sheet_id: int, timeout: int = 60):
    from app.database import SessionLocal

    db = SessionLocal()
    client = AIClient(settings.ai_service_url, timeout)
    try:
        orchestrator = Orchestrator(client, db)
        await orchestrator.process_submission(sheet_id)
    finally:
        await client.close()
        db.close()


def _run_orchestrator_sync(sheet_id: int, timeout: int = 60):
    asyncio.run(_run_orchestrator(sheet_id, timeout))


@router.post("/save", response_model=AnswerSaveResponse)
def save_answer(body: AnswerSaveRequest, db: Session = Depends(get_db)):
    try:
        answer = crud.save_answer(db, body.sheet_id, body.question_id, body.answer_text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnswerSaveResponse(answer_id=answer.answer_id, saved_at=answer.saved_at)


@router.post("/submit")
def submit_answers(
    body: AnswerSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    rows = crud.get_sheet_rows(db, body.sheet_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Sheet not found")
    if any(r.submitted_at for r in rows):
        raise HTTPException(status_code=400, detail="Already submitted")
    if not all(r.answer_id for r in rows):
        raise HTTPException(status_code=400, detail="Not all questions answered")

    crud.submit_sheet(db, body.sheet_id)
    from app.services.audit import log_event

    log_event(
        db,
        action="answers.submit",
        message=f"Sheet {body.sheet_id} submitted for AI check",
        extra={"sheet_id": body.sheet_id},
    )
    settings = crud.get_system_settings(db)
    timeout = int(settings.get("ai_timeout_sec", settings.get("AI_TIMEOUT", "60")))
    background_tasks.add_task(_run_orchestrator_sync, body.sheet_id, timeout)
    return {"status": "submitted", "sheet_id": body.sheet_id}
