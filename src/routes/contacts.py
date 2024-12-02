import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import User
from src.schemas import Contact, ContactCreate
from src.repository import contacts as repository_contacts
from src.repository import users as repository_users

router = APIRouter(prefix="/contacts", tags=["contacts"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
    ):
    try:
        logger.info(f"Received request to create contact: {contact.dict()}")
        logger.info(f"Current user: {current_user.id}")
        result = repository_contacts.create_contact(db=db, contact=contact, user_id=current_user.id)
        logger.info(f"Contact created successfully: {result.__dict__}")
        return result
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}", exc_info=True)
        raise

# Contacts Features
@router.get("/", response_model=List[Contact])
def read_contacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    try:
        logger.info(f"Received request to get contacts for user {current_user.id}")
        contacts = repository_contacts.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
        return contacts
    except SQLAlchemyError as e:
        logger.error(f"Error getting contacts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occured while querying contacts."
            )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the request."
        )

@router.get("/{contact_id}", response_model=Contact)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    db_contact = repository_contacts.get_contact(db, user_id=current_user.id, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return db_contact

@router.put("/{contact_id}", response_model=Contact)
def update_contact(
    contact_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    db_contact = repository_contacts.update_contact(db, user_id=current_user.id, contact_id=contact_id, contact=contact)
    if db_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return db_contact

@router.delete("/{contact_id}", response_model=Contact)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    db_contact = repository_contacts.delete_contact(db, user_id=current_user.id, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    return db_contact

@router.get("/search/", response_model=List[Contact])
def search_contacts(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    contacts = repository_contacts.search_contacts(db, user_id=current_user.id, query=query)
    return contacts

@router.get("/upcoming_birthdays/", response_model=List[Contact])
def get_upcoming_birthdays(
    db: Session = Depends(get_db),
    current_user: User = Depends(repository_users.get_user_by_email)
):
    contacts = repository_contacts.get_upcoming_birthdays(db, user_id=current_user.id)
    return contacts