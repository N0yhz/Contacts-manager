"""
Authentication Utility Functions

This module provides functions for user authentication, token generation, 
password management, and user validation in a FastAPI application.

Dependencies:
    - FastAPI modules for dependency injection and exception handling.
    - SQLAlchemy for database interactions.
    - Redis for caching user sessions.
    - Passlib for password hashing.
    - Python-Jose for JWT operations.
    - dotenv for environment variable loading.

Functions:
    - Password Management: `verify_password`, `get_password_hash`
    - Token Operations: `create_access_token`, `create_verification_token`, 
      `create_password_reset_token`, `verify_token`
    - User Management: `get_current_user`, `authenticate_user`, `require_verified_user`

"""

import os
import pickle
import redis
from dotenv import load_dotenv
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import User
from src.repository import users as users_repo

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

r = redis.Redis(
    host = os.getenv("REDIS_HOST", "redis"),
    port = int(os.getenv("REDIS_PORT", 6379)),
    db = 0,
    decode_responses=False
)

def verify_password(plain_password, hashed_password):
    """
    Verify a plain text password against a hashed password.

    :param plain_password: The plain text password to verify.
    :type plain_password: str
    :param hashed_password: The hashed password from the database.
    :type hashed_password: str
    :return: True if the password matches, False otherwise.
    :rtype: bool
    
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Hash a plain text password using bcrypt.

    :param password: The plain text password to hash.
    :type password: str
    :return: The hashed password.
    :rtype: str
    
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.

    :param data: Data to include in the token payload.
    :type data: dict
    :param expires_delta: Optional expiration duration for the token.
    :type expires_delta: Optional[timedelta]
    :return: The encoded JWT token.
    :rtype: str
    
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_verification_token(email:str) -> str:
    """
    Generate a verification token for a user's email.

    :param email: The email address to encode in the token.
    :type email: str
    :return: The encoded JWT token for email verification.
    :rtype: str
    
    """
    expire = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "verification",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_password_reset_token(email:str) -> str:
    """
    Generate a password reset token.

    :param email: The email address to encode in the token.
    :type email: str
    :return: The encoded JWT token for password reset.
    :rtype: str
    
    """
    expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token:str, expected_type: str = "verification") -> Optional[str]:
    """
    Verify the validity of a JWT token and its type.

    :param token: The JWT token to verify.
    :type token: str
    :param expected_type: The expected type of the token.
    :type expected_type: str
    :return: The email address if the token is valid, None otherwise.
    :rtype: Optional[str]
    
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != expected_type:
            return None
        return email
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Retrieve the current authenticated user based on the JWT token.

    :param token: The JWT token provided by the user.
    :type token: str
    :param db: Database session to fetch user details.
    :type db: Session
    :return: The authenticated user object.
    :rtype: User
    :raises HTTPException: If the token is invalid or the user is not found.
    
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
        
    user = r.get(f"user:{email}")
    if user is None:
        user = users_repo.get_user_by_email(db, email)
        if user is None:
            raise credentials_exception
        r.set(f"user:{email}", pickle.dumps(user))
        r.expire(f"user:{email}", 900)  # 15 minutes expiration
    else:
        user = pickle.loads(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user using email and password.

    :param db: Database session to fetch user details.
    :type db: Session
    :param email: The user's email address.
    :type email: str
    :param password: The user's password.
    :type password: str
    :return: The authenticated user object if credentials are valid, None otherwise.
    :rtype: Optional[User]
    
    """
    user = users_repo.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def require_verified_user(current_user: User = Depends(get_current_user)):
    """
    Ensure the current user has a verified email.

    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The verified user.
    :rtype: User
    :raises HTTPException: If the user's email is not verified.
    
    """

    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified"
        )
    return current_user