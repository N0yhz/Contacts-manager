"""
Authentication and User Management Endpoints

This module defines routes and functions for user authentication, registration, 
email verification, password reset, and profile management in a FastAPI application.

Dependencies:
    - FastAPI modules for routing, dependency injection, and request/response handling.
    - SQLAlchemy for database interactions.
    - Custom repositories and services for user operations, token generation, and email handling.

Routes:
    - POST /register: Register a new user.
    - POST /token: Authenticate user and return access token.
    - GET /verify/{token}: Verify email using a token.
    - POST /resend-verification: Resend email verification link.
    - GET /login: Render login page.
    - POST /forgot-password: Initiate password reset process.
    - GET /reset-password/{token}: Render password reset page.
    - POST /reset-password/{token}: Reset user password.
    - POST /update-avatar: Update user's avatar.
    - GET /me: Retrieve current authenticated user details.
"""

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
from src.services.cloudinary import upload_image

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/services/templates")
templates_2 = Jinja2Templates(directory="src/templates")

@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send a verification email.

    :param user: The user data to create a new account.
    :type user: UserCreate
    :param db: Database session used for the operation.
    :type db: Session
    :return: The newly created user.
    :rtype: UserOut
    :raises HTTPException: If the email is already registered
    
    """
    db_user = users_repo.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail = "Email already registered")
    verification_token = create_verification_token(user.email)
    new_user = users_repo.create_user(db=db, user=user, verification_token=verification_token)
    await send_verification_email(new_user.email, verification_token)

    if new_user.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID not set") 
    print(f"Response user id: {new_user.id}")

    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and provide an access token.

    :param form_data: OAuth2 form data with username and password.
    :type form_data: OAuth2PasswordRequestForm
    :param db: Database session for authentication.
    :type db: Session
    :return: Access token and token type.
    :rtype: Token
    :raises HTTPException: If authentication fails.
    
    """
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
    """
    Verify a user's email using the provided token.

    :param token: The verification token.
    :type token: str
    :param db: Database session used to update user verification status.
    :type db: Session
    :return: Success message on verification.
    :rtype: dict
    :raises HTTPException: If the token is invalid or user not found.
    
    """
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
    """
    Resend the email verification link to the user.

    :param email_schema: Email address of the user.
    :type email_schema: EmailSchema
    :param db: Database session used to fetch user details.
    :type db: Session
    :return: Success message on resending verification email.
    :rtype: dict
    :raises HTTPException: If the user is not found or already verified.
    
    """
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
    """
    Render the login page.

    :param request: HTTP request object.
    :type request: Request
    :param reset: Optional query parameter for reset status.
    :type reset: str
    :return: Rendered HTML page.
    :rtype: HTMLResponse
    
    """
    return templates_2.TemplateResponse("login.html", {"request": request, "reset": reset})

@router.post("/forgot-password")
async def forgot_password(email_schema: EmailSchema, db: Session = Depends(get_db)):
    """
    Initiate the password reset process.

    :param email_schema: Email address of the user.
    :type email_schema: EmailSchema
    :param db: Database session used to fetch user details.
    :type db: Session
    :return: Message indicating the status of the password reset process.
    :rtype: dict
    
    """
    user = users_repo.get_user_by_email(db, email_schema.email)
    if user:
        reset_token = create_password_reset_token(email_schema.email)
        users_repo.update_reset_token(db, email_schema.email, reset_token)
        await send_password_reset_email(email_schema.email, reset_token)
    return {"message": "If the email exists, a password reset link will be sent"}

@router.get("/reset-password/{token}")
async def reset_password_page(request:Request, token:str):
    """
    Render the password reset page.

    :param request: HTTP request object.
    :type request: Request
    :param token: Password reset token.
    :type token: str
    :return: Rendered HTML page.
    :rtype: HTMLResponse
    
    """
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})

@router.post("/reset-password/{token}")
async def reset_password(
    request: Request,
    token: str,
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
    ):
    """
    Reset a user's password using the provided token.

    :param request: HTTP request object.
    :type request: Request
    :param token: Password reset token.
    :type token: str
    :param password: New password.
    :type password: str
    :param confirm_password: Confirmation of the new password.
    :type confirm_password: str
    :param db: Database session used to update the user's password.
    :type db: Session
    :return: Redirects to the login page on success.
    :rtype: RedirectResponse
    
    """

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

@router.post("/update-avatar", response_model=UserOut)
async def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
        """
        Update the user's avatar image.

        :param file: Image file uploaded by the user.
        :type file: UploadFile
        :param db: Database session used to update user details.
        :type db: Session
        :param current_user: The currently authenticated user.
        :type current_user: User
        :return: The updated user with the new avatar.
        :rtype: UserOut
        :raises HTTPException: If the image upload fails.
        
        """

        try:
            avatar_url = upload_image(file)
            updated_user = users_repo.update_user_avatar(db, current_user.id, avatar_url)
            return updated_user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/me", response_model = UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the details of the currently authenticated user.

    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The authenticated user's details.
    :rtype: UserOut
    
    """
    return current_user