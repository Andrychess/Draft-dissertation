from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base, User
from app.routers import admin, answers, auth, groups, questions, results, sessions, student, templates, users

app = FastAPI(title="AutoAssess IS", version="1.0.0")


@app.on_event("startup")
def startup_db():
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        from app.database import SessionLocal
        from app.auth import hash_password
        from app.models import SystemSetting, UserRole

        db = SessionLocal()
        try:
            if not db.query(User).filter(User.email == "admin@example.com").first():
                db.add(
                    User(
                        email="admin@example.com",
                        password_hash=hash_password("admin123"),
                        full_name="Administrator",
                        role=UserRole.admin,
                    )
                )
            defaults = {
                "ai_timeout_sec": "60",
                "passing_threshold": "0.6",
                "confidence_threshold": "0.7",
            }
            for key, value in defaults.items():
                if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
                    db.add(SystemSetting(key=key, value=value))
            db.commit()
        finally:
            db.close()

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(templates.router)
app.include_router(questions.router)
app.include_router(sessions.router)
app.include_router(answers.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(results.router)


@app.get("/health")
def health():
    return {"status": "ok"}
