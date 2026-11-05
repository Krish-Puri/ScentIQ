"""SCENTIQ Authentication Endpoints.
Provides token creation, password hashing, and user registration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, UserTokenPayload
from app.db.session import get_db
from app.schemas.envelope import ResponseEnvelope
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=ResponseEnvelope[TokenResponse])
def register(data: UserRegisterRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    token_resp = service.register(data)
    return ResponseEnvelope.success(data=token_resp)


@router.post("/token", response_model=ResponseEnvelope[TokenResponse])
@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(data: UserLoginRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    token_resp = service.authenticate(data.email, data.password)
    return ResponseEnvelope.success(data=token_resp)


@router.get("/me", response_model=ResponseEnvelope[dict])
def get_current_user_profile(user: UserTokenPayload = Depends(get_current_user)):
    return ResponseEnvelope.success(data={"user_id": user.sub, "email": user.email, "role": user.role})

