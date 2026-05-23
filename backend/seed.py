"""Create default admin user and system settings."""
from app.auth import hash_password
from app.database import SessionLocal
from app.models import SystemSetting, User, UserRole


def main():
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
        print("Created admin@example.com / admin123 and default settings")
    finally:
        db.close()


if __name__ == "__main__":
    main()
