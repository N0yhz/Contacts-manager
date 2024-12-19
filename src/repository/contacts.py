"""
Contacts Repository Module

This module provides database operations for managing contacts in the application.

Dependencies:
    - SQLAlchemy for database interactions
    - Logging for error tracking
    - Application-specific schemas and models

Functions:
    - get_contacts: Retrieve contacts for a user
    - create_contact: Create a new contact
    - get_contact: Retrieve a specific contact
    - update_contact: Update an existing contact
    - delete_contact: Delete a contact
    - search_contacts: Search for contacts
    - get_upcoming_birthdays: Retrieve contacts with upcoming birthdays

"""

import logging

from datetime import date, timedelta

from sqlalchemy import or_, extract, and_
from sqlalchemy.orm import Session

from src.database.models import Contact
from src.schemas import ContactCreate

logger = logging.getLogger(__name__)

def get_contacts(db: Session, user_id: int, skip: int=0, limit: int=100):
    """
    Retrieve contacts for a specific user with pagination.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user whose contacts to retrieve
    :type user_id: int
    :param skip: Number of records to skip (for pagination)
    :type skip: int
    :param limit: Maximum number of records to return
    :type limit: int
    :return: List of Contact objects
    :rtype: list
    
    """
    return db.query(Contact).filter(
        Contact.owner_id == user_id
    ).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: ContactCreate, user_id: str):
    """
    Create a new contact for a user.

    :param db: Database session
    :type db: Session
    :param contact: Contact data
    :type contact: ContactCreate
    :param user_id: ID of the user creating the contact
    :type user_id: str
    :return: Created Contact object
    :rtype: Contact
    
    """
    db_contact = Contact(first_name=contact.first_name,
        last_name=contact.last_name,
        phone_number=contact.phone_number,
        email=contact.email,
        birthday=contact.birthday,
        additional_data=contact.additional_data,
        owner_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, user_id: int, contact_id: int):
    """
    Retrieve a specific contact for a user.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: int
    :param contact_id: ID of the contact to retrieve
    :type contact_id: int
    :return: Contact object if found, else None
    :rtype: Contact or None
    
    """
    return db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.owner_id == user_id
    ).first()

def update_contact(db: Session, user_id: int, contact_id: int, contact: ContactCreate):
    """
    Update an existing contact.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: int
    :param contact_id: ID of the contact to update
    :type contact_id: int
    :param contact: Updated contact data
    :type contact: ContactCreate
    :return: Updated Contact object if found, else None
    :rtype: Contact or None
    
    """
    db_contact = get_contact(db, user_id, contact_id)
    if db_contact:
        for key, value in contact.dict().items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, user_id: int, contact_id: int):
    """
    Delete a specific contact.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: int
    :param contact_id: ID of the contact to delete
    :type contact_id: int
    :return: Deleted Contact object if found, else None
    :rtype: Contact or None
    
    """
    db_contact = get_contact(db, user_id, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, user_id: int, query: int):
    """
    Search for contacts based on a query string.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: int
    :param query: Search query string
    :type query: int
    :return: List of matching Contact objects
    :rtype: list
    
    """
    return db.query(Contact).filter(
        Contact.owner_id == user_id,
        or_(
            Contact.first_name.ilike(f"%{query}%"),
            Contact.last_name.ilike(f"%{query}%"),
            Contact.email.ilike(f"%{query}%"),
            Contact.phone_number.ilike(f"%{query}%")
        )
    ).all()

def get_upcoming_birthdays(db: Session, user_id: int):
    """
    Retrieve contacts with birthdays in the next 7 days.

    :param db: Database session
    :type db: Session
    :param user_id: ID of the user
    :type user_id: int
    :return: List of Contact objects with upcoming birthdays
    :rtype: list
    
    """
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