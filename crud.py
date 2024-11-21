from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_, extract, and_
from datetime import date, timedelta
import models, schemas
import logging
from auth import get_password_hash

logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int):
    try:
        logger.info(f"Creating contact: {contact.dict()}")
        logger.info(f"User ID: {user_id}")
        db_contact = models.Contact(**contact.dict(), owner_id=user_id)
        logger.info(f"Contact object created: {db_contact.__dict__}")
        db.add(db_contact)
        logger.info("Contact added to session")
        db.commit()
        logger.info("Session committed")
        db.refresh(db_contact)
        logger.info(f"Contact refreshed: {db_contact.__dict__}")
        return db_contact
    except IntegrityError as e:
        logger.error(f"IntegrityError while creating contact: {str(e)}")
        db.rollback()
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError while creating contact: {str(e)}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating contact: {str(e)}")
        db.rollback()
        raise

def get_contact(db: Session, user_id: int, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == user_id).first()

def update_contact(db: Session, user_id: int, contact_id: int, contact: schemas.ContactCreate):
    db_contact = get_contact(db, user_id, contact_id)
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, user_id: int, contact_id: int):
    db_contact = get_contact(db, user_id, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, user_id: int, query: str):
    return db.query(models.Contact).filter(
        models.Contact.owner_id == user_id,
        or_(
            models.Contact.first_name.ilike(f"%{query}%"),
            models.Contact.last_name.ilike(f"%{query}%"),
            models.Contact.email.ilike(f"%{query}%")
        )
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    today = date.today()
    seven_days_later = today + timedelta(days=7)
    
    if seven_days_later.year > today.year:
        condition1 = and_(
            extract('month', models.Contact.birthday) == today.month,
            extract('day', models.Contact.birthday) >= today.day
        )
        condition2 = and_(
            extract('month', models.Contact.birthday) == seven_days_later.month,
            extract('day', models.Contact.birthday) <= seven_days_later.day
        )
        upcoming_birthdays = db.query(models.Contact).filter(
            models.Contact.owner_id == user_id,
            or_(condition1, condition2)
        ).all()
    else:
        upcoming_birthdays = db.query(models.Contact).filter(
            models.Contact.owner_id == user_id,
            and_(
                extract('month', models.Contact.birthday) >= today.month,
                extract('day', models.Contact.birthday).between(today.day, seven_days_later.day)
            )
        ).all()
    
    return upcoming_birthdays