from sqlalchemy.orm import Session
from sqlalchemy import or_, extract, and_
from datetime import date, timedelta
import models, schemas

def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

def get_contacts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Contact).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: schemas.ContactCreate):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    for key, value in contact.dict().items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    db.delete(db_contact)
    db.commit()
    return db_contact

def search_contacts(db: Session, query: str):
    return db.query(models.Contact).filter(
        or_(
            models.Contact.first_name.ilike(f"%{query}%"),
            models.Contact.last_name.ilike(f"%{query}%"),
            models.Contact.email.ilike(f"%{query}%")
        )
    ).all()

def get_upcoming_birthdays(db: Session):
    today = date.today()
    seven_days_later = today + timedelta(days=7)
    
    # Handle year rollover
    if seven_days_later.year > today.year:
        # Birthdays from today to end of year
        condition1 = and_(
            extract('month', models.Contact.birthday) == today.month,
            extract('day', models.Contact.birthday) >= today.day
        )
        # Birthdays from start of year to seven days later
        condition2 = and_(
            extract('month', models.Contact.birthday) == seven_days_later.month,
            extract('day', models.Contact.birthday) <= seven_days_later.day
        )
        upcoming_birthdays = db.query(models.Contact).filter(or_(condition1, condition2)).all()
    else:
        # Simple case: all birthdays in the next 7 days
        upcoming_birthdays = db.query(models.Contact).filter(
            and_(
                extract('month', models.Contact.birthday) >= today.month,
                extract('day', models.Contact.birthday).between(today.day, seven_days_later.day)
            )
        ).all()
    
    return upcoming_birthdays