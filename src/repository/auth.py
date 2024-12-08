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
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_verification_token(email:str) -> str:
    expire = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "verification",
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_password_reset_token(email:str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token:str, expected_type: str = "verification") -> Optional[str]:
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
    user = users_repo.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def require_verified_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified"
        )
    return current_user