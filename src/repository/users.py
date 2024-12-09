import logging

from sqlalchemy.orm import Session
from src.database.models import User, Contact
from src.schemas import UserCreate
from src.repository.auth import get_password_hash

logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate, verification_token:str):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        verification_token=verification_token,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_user(db: Session, email:str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_verification_token(db: Session, email: str, new_token: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = new_token
        db.commit()
        db.refresh(user)
    return user

def update_reset_token(db: Session, email: str, reset_token: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = reset_token
        db.commit()
        db.refresh(user)
    return user

def clear_reset_token(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_user_avatar(db: Session, user_id: str, avatar_url: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
    return user

def update_password(db: Session, email:str, new_password: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: str):
    try:
        db.query(Contact).filter(Contact.owner_id == user_id).delete()
         
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise

