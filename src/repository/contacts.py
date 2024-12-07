import logging

from datetime import date, timedelta

from sqlalchemy import or_, extract, and_
from sqlalchemy.orm import Session

from src.database.models import Contact
from src.schemas import ContactCreate

logger = logging.getLogger(__name__)

def get_contacts(db: Session, user_id: int, skip: int=0, limit: int=100):
    return db.query(Contact).filter(
        Contact.owner_id == user_id
    ).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: ContactCreate, user_id: str):
    db_contact = Contact(**contact.dict(), owner_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, user_id: int, contact_id: int):
    return db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.owner_id == user_id
    ).first()

def update_contact(db: Session, user_id: int, contact_id: int, contact: ContactCreate):
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

def search_contacts(db: Session, user_id: int, query: int):
    return db.query(Contact).filter(
        Contact.owner_id == user_id,
        or_(
            Contact.first_name.ilike(f"%{query}%"),
            Contact.last_name.ilike(f"%{query}%"),
            Contact.email.ilike(f"%{query}%")
        )
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    today = date.today()
    seven_days_later = today + timedelta(days=7)
    
    if seven_days_later.year > today.year:
        condition1 = and_(
            extract('month', Contact.birthday) == today.month,
            extract('day', Contact.birthday) >= today.day
        )
        condition2 = and_(
            extract('month', Contact.birthday) == seven_days_later.month,
            extract('day', Contact.birthday) <= seven_days_later.day
        )
        upcoming_birthdays = db.query(Contact).filter(
            Contact.owner_id == user_id,
            or_(condition1, condition2)
        ).all()
    else:
        upcoming_birthdays = db.query(Contact).filter(
            Contact.owner_id == user_id,
            and_(
                extract('month', Contact.birthday) >= today.month,
                extract('day', Contact.birthday).between(today.day, seven_days_later.day)
            )
        ).all()
    return upcoming_birthdays