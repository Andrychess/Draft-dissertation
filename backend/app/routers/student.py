from fastapi import APIRouter, HTTPException

from app import crud
from app.database import SessionLocal
from app.schemas import StudentResultItem

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/results/{sheet_id}", response_model=list[StudentResultItem])
def student_results(sheet_id: int):
    db = SessionLocal()
    try:
        rows = crud.get_sheet_rows(db, sheet_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Sheet not found")
        if not rows[0].submitted_at:
            raise HTTPException(status_code=400, detail="Answers not submitted yet")
        return crud.get_student_results(db, sheet_id, rows=rows)
    finally:
        db.close()


@router.get("/results/{sheet_id}/status")
def student_results_status(sheet_id: int):
    db = SessionLocal()
    try:
        rows = crud.get_sheet_rows(db, sheet_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Sheet not found")
        submitted = bool(rows[0].submitted_at)
        ai_count = sum(1 for r in rows if r.ai_results)
        total = len(rows)
        ready = submitted and ai_count >= total
        return {"submitted": submitted, "ready": ready, "checked": ai_count, "total": total}
    finally:
        db.close()
