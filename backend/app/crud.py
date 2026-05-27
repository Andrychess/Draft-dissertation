import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import hash_password
from app.models import (
    AICheckResult,
    AnswerSheet,
    AssessmentTemplate,
    LectureMaterial,
    Question,
    Session,
    SessionGroup,
    SessionStatus,
    StudentAnswer,
    StudyGroup,
    User,
    UserRole,
    Verdict,
)


def _generate_connection_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# Users
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def list_users(db: Session) -> List[User]:
    return db.query(User).order_by(User.id).all()


def create_user(db: Session, email: str, password: str, full_name: str, role: UserRole) -> User:
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, **kwargs) -> User:
    if "password" in kwargs and kwargs["password"]:
        user.password_hash = hash_password(kwargs.pop("password"))
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


# Groups
def list_groups(db: Session) -> List[StudyGroup]:
    return db.query(StudyGroup).order_by(StudyGroup.cipher).all()


def create_group(db: Session, cipher: str, name: str) -> StudyGroup:
    group = StudyGroup(cipher=cipher, name=name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


# Templates
def list_templates(db: Session, user_id: Optional[int] = None) -> List[AssessmentTemplate]:
    q = db.query(AssessmentTemplate)
    if user_id:
        q = q.filter(AssessmentTemplate.created_by == user_id)
    return q.order_by(AssessmentTemplate.created_at.desc()).all()


def get_template(db: Session, template_id: int) -> Optional[AssessmentTemplate]:
    return (
        db.query(AssessmentTemplate)
        .options(joinedload(AssessmentTemplate.questions))
        .filter(AssessmentTemplate.id == template_id)
        .first()
    )


def create_template(db: Session, name: str, created_by: int, material_id: Optional[int], **extra) -> AssessmentTemplate:
    tpl = AssessmentTemplate(name=name, created_by=created_by, material_id=material_id, **extra)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def update_template(db: Session, tpl: AssessmentTemplate, **kwargs) -> AssessmentTemplate:
    for key, value in kwargs.items():
        if value is not None:
            setattr(tpl, key, value)
    db.commit()
    db.refresh(tpl)
    return tpl


def delete_template(db: Session, tpl: AssessmentTemplate) -> None:
    db.delete(tpl)
    db.commit()


def add_question(db: Session, template_id: int, **data) -> Question:
    q = Question(template_id=template_id, **data)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()


def update_question(db: Session, question: Question, **kwargs) -> Question:
    for key, value in kwargs.items():
        if value is not None:
            setattr(question, key, value)
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question: Question) -> None:
    db.delete(question)
    db.commit()


def add_lecture_material(db: Session, title: str, file_path: str, uploaded_by: int) -> LectureMaterial:
    material = LectureMaterial(title=title, file_path=file_path, uploaded_by=uploaded_by)
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


# Sessions
def list_sessions(db: Session, user_id: Optional[int] = None) -> List[Session]:
    q = db.query(Session)
    if user_id:
        q = q.filter(Session.created_by == user_id)
    return q.order_by(Session.id.desc()).all()


def get_session_by_code(db: Session, code: str) -> Optional[Session]:
    return (
        db.query(Session)
        .options(joinedload(Session.template).joinedload(AssessmentTemplate.questions))
        .filter(Session.connection_code == code.upper())
        .first()
    )


def get_session(db: Session, session_id: int) -> Optional[Session]:
    return (
        db.query(Session)
        .options(joinedload(Session.template).joinedload(AssessmentTemplate.questions))
        .filter(Session.id == session_id)
        .first()
    )


def create_session(
    db: Session,
    name: str,
    template_id: int,
    created_by: int,
    group_ciphers: List[str],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
) -> Session:
    session = Session(
        name=name,
        connection_code=_generate_connection_code(),
        template_id=template_id,
        created_by=created_by,
        start_time=start_time,
        end_time=end_time,
        status=SessionStatus.planned,
    )
    db.add(session)
    db.flush()
    for cipher in group_ciphers:
        db.add(SessionGroup(session_id=session.id, group_cipher=cipher))
    db.commit()
    db.refresh(session)
    return session


def extend_session(db: Session, session: Session, end_time: datetime) -> Session:
    session.end_time = end_time
    if session.status == SessionStatus.finished:
        session.status = SessionStatus.active
    db.commit()
    db.refresh(session)
    return session


def finish_session(db: Session, session: Session) -> Session:
    session.status = SessionStatus.finished
    session.end_time = session.end_time or datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def activate_session_if_needed(db: Session, session: Session) -> Session:
    if session.status == SessionStatus.planned:
        session.status = SessionStatus.active
        session.start_time = session.start_time or datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def format_student_name(
    student_name: str,
    last_name: Optional[str] = None,
    first_name: Optional[str] = None,
    patronymic: Optional[str] = None,
) -> str:
    if last_name and first_name:
        parts = [last_name, first_name]
        if patronymic:
            parts.append(patronymic)
        return " ".join(parts)
    return student_name


def join_session(
    db: Session,
    session: Session,
    student_name: str,
    group_cipher: Optional[str],
    last_name: Optional[str] = None,
    first_name: Optional[str] = None,
    patronymic: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
) -> tuple[int, int]:
    student_name = format_student_name(student_name, last_name, first_name, patronymic)
    session = activate_session_if_needed(db, session)
    existing_sheet_id = (
        db.query(AnswerSheet.sheet_id)
        .filter(
            AnswerSheet.session_id == session.id,
            AnswerSheet.student_name == student_name,
        )
        .first()
    )
    if existing_sheet_id:
        return session.id, existing_sheet_id[0]

    questions = session.template.questions
    if not questions:
        raise ValueError("Session template has no questions")

    sheet_id = (db.query(func.max(AnswerSheet.sheet_id)).scalar() or 0) + 1
    first_q = questions[0]
    sheet_kwargs = dict(
        sheet_id=sheet_id,
        session_id=session.id,
        student_name=student_name,
        last_name=last_name,
        first_name=first_name,
        patronymic=patronymic,
        group_cipher=group_cipher,
        device_fingerprint=device_fingerprint,
    )
    db.add(AnswerSheet(question_id=first_q.id, **sheet_kwargs))

    for q in questions[1:]:
        db.add(AnswerSheet(question_id=q.id, **sheet_kwargs))
    db.commit()
    return session.id, sheet_id


def get_sheet_rows(db: Session, sheet_id: int) -> List[AnswerSheet]:
    return (
        db.query(AnswerSheet)
        .options(
            joinedload(AnswerSheet.student_answer),
            joinedload(AnswerSheet.question),
            joinedload(AnswerSheet.ai_results),
        )
        .filter(AnswerSheet.sheet_id == sheet_id)
        .all()
    )


def save_answer(db: Session, sheet_id: int, question_id: int, answer_text: str) -> StudentAnswer:
    row = (
        db.query(AnswerSheet)
        .options(joinedload(AnswerSheet.student_answer))
        .filter(AnswerSheet.sheet_id == sheet_id, AnswerSheet.question_id == question_id)
        .first()
    )
    if not row:
        raise ValueError("Answer sheet row not found")

    if row.answer_id and row.student_answer:
        answer = row.student_answer
        answer.answer_text = answer_text
        answer.saved_at = datetime.now(timezone.utc)
    elif row.answer_id:
        answer = db.query(StudentAnswer).filter(StudentAnswer.answer_id == row.answer_id).first()
        if not answer:
            raise ValueError("Student answer not found")
        answer.answer_text = answer_text
        answer.saved_at = datetime.now(timezone.utc)
    else:
        answer = StudentAnswer(answer_text=answer_text)
        db.add(answer)
        db.flush()
        row.answer_id = answer.answer_id

    db.commit()
    db.refresh(answer)
    return answer


def submit_sheet(db: Session, sheet_id: int) -> List[AnswerSheet]:
    rows = db.query(AnswerSheet).filter(AnswerSheet.sheet_id == sheet_id).all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.submitted_at = now
    db.commit()
    return rows


def get_session_results(db: Session, session_id: int) -> List[dict]:
    rows = (
        db.query(AnswerSheet)
        .options(joinedload(AnswerSheet.question))
        .filter(AnswerSheet.session_id == session_id)
        .all()
    )
    by_sheet: dict[int, list[AnswerSheet]] = {}
    for row in rows:
        by_sheet.setdefault(row.sheet_id, []).append(row)

    sheet_ids = list(by_sheet.keys())
    ai_by_sheet: dict[int, list[AICheckResult]] = {sid: [] for sid in sheet_ids}
    if sheet_ids:
        for ai in db.query(AICheckResult).filter(AICheckResult.sheet_id.in_(sheet_ids)).all():
            ai_by_sheet.setdefault(ai.sheet_id, []).append(ai)

    results = []
    for sheet_id, sheet_rows in by_sheet.items():
        first = sheet_rows[0]
        ai_rows = ai_by_sheet.get(sheet_id, [])
        max_score = sum(r.question.max_score for r in sheet_rows if r.question)
        total = sum((r.corrected_score or r.score) for r in ai_rows)
        verdicts = [r.verdict.value for r in ai_rows]
        verdict = "review" if "review" in verdicts else ("failed" if "failed" in verdicts else "passed")
        results.append(
            {
                "sheet_id": sheet_id,
                "student_name": first.student_name,
                "group_cipher": first.group_cipher,
                "total_score": total,
                "max_score": max_score,
                "verdict": verdict if ai_rows else None,
            }
        )
    return results


def get_result_detail(db: Session, sheet_id: int, question_id: int) -> Optional[AnswerSheet]:
    return (
        db.query(AnswerSheet)
        .options(
            joinedload(AnswerSheet.student_answer),
            joinedload(AnswerSheet.ai_results),
            joinedload(AnswerSheet.question),
        )
        .filter(AnswerSheet.sheet_id == sheet_id, AnswerSheet.question_id == question_id)
        .first()
    )


def get_ai_result(db: Session, check_id: int) -> Optional[AICheckResult]:
    return db.query(AICheckResult).filter(AICheckResult.check_id == check_id).first()


def approve_result(db: Session, result: AICheckResult, user_id: int) -> AICheckResult:
    result.approved_by = user_id
    result.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(result)
    return result


def correct_result(db: Session, result: AICheckResult, corrected_score: float, explanation: Optional[str]) -> AICheckResult:
    if result.approved_at is not None:
        raise ValueError("Result already approved and cannot be modified")
    result.corrected_score = corrected_score
    if explanation:
        result.explanation = explanation
    db.commit()
    db.refresh(result)
    return result


def create_ai_check_result(db: Session, **kwargs) -> AICheckResult:
    result = AICheckResult(**kwargs)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def create_ai_check_results_bulk(db: Session, items: List[dict]) -> List[AICheckResult]:
    if not items:
        return []
    results = [AICheckResult(**item) for item in items]
    db.add_all(results)
    db.commit()
    for result in results:
        db.refresh(result)
    return results


def list_system_logs(db: Session, limit: int = 100) -> List:
    from app.models import SystemLog

    return db.query(SystemLog).order_by(SystemLog.id.desc()).limit(limit).all()


def get_system_settings(db: Session) -> dict[str, str]:
    from app.models import SystemSetting

    return {row.key: row.value for row in db.query(SystemSetting).all()}


def update_system_settings(db: Session, values: dict[str, str]) -> dict[str, str]:
    from app.models import SystemSetting
    from app.services.cache import invalidate_settings_cache

    for key, value in values.items():
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    db.commit()
    invalidate_settings_cache()
    return get_system_settings(db)


def get_student_results(db: Session, sheet_id: int, rows: Optional[List[AnswerSheet]] = None) -> List[dict]:
    if rows is None:
        rows = get_sheet_rows(db, sheet_id)
    if not rows:
        return []
    out = []
    for row in rows:
        ai = row.ai_results[0] if row.ai_results else None
        out.append(
            {
                "question_id": row.question_id,
                "question_text": row.question.text if row.question else "",
                "max_score": row.question.max_score if row.question else 0,
                "answer_text": row.student_answer.answer_text if row.student_answer else None,
                "submitted_at": row.submitted_at,
                "score": (ai.corrected_score or ai.score) if ai else None,
                "confidence": ai.confidence if ai else None,
                "verdict": ai.verdict.value if ai else None,
                "explanation": ai.explanation if ai else None,
                "weaknesses": ai.weaknesses if ai else [],
                "strengths": ai.strengths if ai else [],
                "details": ai.details if ai else None,
            }
        )
    return out
