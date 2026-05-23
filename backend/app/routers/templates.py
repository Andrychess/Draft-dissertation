import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import require_roles
from app.database import get_db
from app.models import User, UserRole
from app.schemas import (
    QuestionCreate,
    QuestionResponse,
    TemplateCreate,
    TemplateListItem,
    TemplateResponse,
    TemplateUpdate,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/lectures"))


@router.get("", response_model=list[TemplateListItem])
def list_templates(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    if user.role == UserRole.admin:
        return crud.list_templates(db)
    return crud.list_templates(db, user_id=user.id)


@router.post("", response_model=TemplateListItem, status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    return crud.create_template(db, body.name, user.id, body.material_id, **body.model_dump(exclude={"name", "material_id"}))


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    tpl = crud.get_template(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@router.put("/{template_id}", response_model=TemplateListItem)
def update_template(
    template_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    tpl = crud.get_template(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return crud.update_template(db, tpl, **body.model_dump(exclude_unset=True))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    tpl = crud.get_template(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    crud.delete_template(db, tpl)


@router.post("/{template_id}/questions", response_model=QuestionResponse, status_code=201)
def add_question(
    template_id: int,
    body: QuestionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    if not crud.get_template(db, template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    return crud.add_question(db, template_id, **body.model_dump())


@router.post("/{template_id}/lecture")
async def upload_lecture(
    template_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.teacher, UserRole.admin)),
):
    tpl = crud.get_template(db, template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    if not file.filename or not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)

    material = crud.add_lecture_material(db, file.filename, str(dest), user.id)
    crud.update_template(db, tpl, material_id=material.id)

    from app.services.lecture_topics import process_lecture_for_template

    topics_payload = process_lecture_for_template(template_id, str(dest))
    return {
        "material_id": material.id,
        "file_path": str(dest),
        "topics_extracted": topics_payload.get("topic_count", 0),
        "relevance_adapter": "processed",
    }
