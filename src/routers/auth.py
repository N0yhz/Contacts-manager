from sqlalchemy.orm import Session
from src.database.database import get_db
from src.database.models import User
from src.schemas import Token, UserCreate, UserOut, EmailSchema
from src.services.email import send_verification_email, send_password_reset_email
from src.repository import users as users_repo
from src.repository.auth import (
    authenticate_user, get_current_user, create_access_token, create_verification_token,
    verify_token, create_password_reset_token,
)

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/services/templates")
templates_2 = Jinja2Templates(directory="src/templates")

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = users_repo.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail = "Email already registered")
    verification_token = create_verification_token(user.email)
    new_user = users_repo.create_user(db=db, user=user, verification_token=verification_token)
    await send_verification_email(new_user.email, verification_token)
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail = "Incorrect username or password",
                            headers = {"WWW-Authenticate": "Bearer"},
                            )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    email= verify_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail = "Invalid or expired token",
                            )
    user = users_repo.verify_user(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "User not found",
                            )
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(email_schema: EmailSchema, db: Session = Depends(get_db)):
    user = users_repo.get_user_by_email(db, email_schema.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "User not found",
                            )
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail = "Email is already verified",
                            )
    verification_token = create_verification_token(user.email)
    users_repo.update_verification_token(db, user.email, verification_token)
    await send_verification_email(user.email, verification_token)
    return {"message": "Verification email resent successfully"}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, reset: str = None):
    return templates_2.TemplateResponse("login.html", {"request": request, "reset": reset})

@router.post("/forgot-password")
async def forgot_password(email_schema: EmailSchema, db: Session = Depends(get_db)):
    user = users_repo.get_user_by_email(db, email_schema.email)
    if user:
        reset_token = create_password_reset_token(email_schema.email)
        users_repo.update_reset_token(db, email_schema.email, reset_token)
        await send_password_reset_email(email_schema.email, reset_token)
    return {"message": "If the email exists, a password reset link will be sent"}

@router.get("/reset-password/{token}")
async def reset_password_page(request:Request, token:str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.post("/reset-password/{token}")
async def reset_password(
    request: Request,
    token: str,
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
    ):

    if password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Passwords do not match"}
        )

    email = verify_token(token, expected_type = "password_reset")
    if not email:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "Invalid or expired token"}
        )
    
    user = users_repo.update_password(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "reset_password.html",
            {"request": request, "token": token, "error": "User not found"}
        )
    users_repo.clear_reset_token(db, email)
    return RedirectResponse(url="/login?reset=success", status_code= status.HTTP_303_SEE_OTHER)

@router.get("/me", response_model = UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user