from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.auth import create_access_token, create_refresh_token, decode_token, verify_password
from app.database import get_db
from app.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.services.audit import log_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    role = user.role.value
    log_event(
        db,
        action="auth.login",
        message=f"User {user.email} logged in",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=create_access_token(user.email, role),
        refresh_token=create_refresh_token(user.email, role),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    email = payload.get("sub")
    user = crud.get_user_by_email(db, email) if email else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    role = user.role.value
    return TokenResponse(
        access_token=create_access_token(user.email, role),
        refresh_token=create_refresh_token(user.email, role),
    )
