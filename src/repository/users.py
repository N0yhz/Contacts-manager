"""
Users Repository Module

This module provides database operations for managing users in the application.

Dependencies:
    - SQLAlchemy for database interactions
    - Logging for error tracking
    - Application-specific schemas, models, and authentication utilities

Functions:
    - get_user: Retrieve a user by ID
    - get_user_by_email: Retrieve a user by email
    - create_user: Create a new user
    - verify_user: Mark a user as verified
    - update_verification_token: Update a user's verification token
    - update_reset_token: Update a user's password reset token
    - clear_reset_token: Clear a user's password reset token
    - update_user_avatar: Update a user's avatar URL
    - update_password: Update a user's password
    - delete_user: Delete a user and their associated contacts

"""
import logging

from sqlalchemy.orm import Session
from src.database.models import User, Contact
from src.schemas import UserCreate
from src.repository.auth import get_password_hash

logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int):
    """
    Retrieve a user by their ID.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user to retrieve
    :type user_id: int
    :return: User object if found, else None
    :rtype: User or None
    
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by their email address.

    :param db: Database session
    :type db: Session
    :param email: Email address of the user to retrieve
    :type email: str
    :return: User object if found, else None
    :rtype: User or None
    
    """

def create_user(db: Session, user: UserCreate, verification_token:str):
    """
    Create a new user.

    :param db: Database session
    :type db: Session
    :param user: User data
    :type user: UserCreate
    :param verification_token: Token for email verification
    :type verification_token: str
    :return: Created User object
    :rtype: User
    
    """
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
    print(f"User created with ID: {db_user.id}")
    return db_user

def verify_user(db: Session, email:str):
    """
    Mark a user as verified.

    :param db: Database session
    :type db: Session
    :param email: Email of the user to verify
    :type email: str
    :return: Updated User object if found, else None
    :rtype: User or None
    
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_verification_token(db: Session, email: str, new_token: str):
    """
    Update a user's verification token.

    :param db: Database session
    :type db: Session
    :param email: Email of the user
    :type email: str
    :param new_token: New verification token
    :type new_token: str
    :return: Updated User object if found, else None
    :rtype: User or None
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = new_token
        db.commit()
        db.refresh(user)
    return user

def update_reset_token(db: Session, email: str, reset_token: str):
    """
    Update a user's password reset token.

    :param db: Database session
    :type db: Session
    :param email: Email of the user
    :type email: str
    :param reset_token: New password reset token
    :type reset_token: str
    :return: Updated User object if found, else None
    :rtype: User or None
    
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = reset_token
        db.commit()
        db.refresh(user)
    return user

def clear_reset_token(db: Session, email: str):
    """
    Clear a user's password reset token.

    :param db: Database session
    :type db: Session
    :param email: Email of the user
    :type email: str
    :return: Updated User object if found, else None
    :rtype: User or None
    
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.verification_token = None
        db.commit()
        db.refresh(user)
    return user

def update_user_avatar(db: Session, user_id: str, avatar_url: str):
    """
    Update a user's avatar URL.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: str
    :param avatar_url: New avatar URL
    :type avatar_url: str
    :return: Updated User object if found, else None
    :rtype: User or None
    
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
    return user

def update_password(db: Session, email:str, new_password: str):
    """
    Update a user's password.

    :param db: Database session
    :type db: Session
    :param email: Email of the user
    :type email: str
    :param new_password: New password (plain text)
    :type new_password: str
    :return: Updated User object if found, else None
    :rtype: User or None
    
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: str):
    """
    Delete a user and their associated contacts.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user to delete
    :type user_id: str
    :return: True if user was deleted, False if user was not found
    :rtype: bool
    :raises Exception: If there's an error during the deletion process
    
    """
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
