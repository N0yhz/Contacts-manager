"""
Contacts Management Endpoints

This module provides CRUD (Create, Read, Update, Delete) operations and additional features 
for managing user contacts in a FastAPI application.

Dependencies:
    - FastAPI modules for routing, dependency injection, and request/response handling.
    - SQLAlchemy for database interactions.
    - Custom repositories for contact-related database operations.
    - Utilities for rate-limiting requests.

Routes:
    - POST /contacts/: Create a new contact.
    - GET /contacts/: Retrieve all contacts with optional pagination.
    - GET /contacts/{contact_id}: Retrieve details of a specific contact.
    - PUT /contacts/{contact_id}: Update a contact's details.
    - DELETE /contacts/{contact_id}: Delete a specific contact.
    - GET /contacts/search: Search contacts by a query string.
    - GET /contacts/upcoming-birthdays: Retrieve contacts with upcoming birthdays within a specified number of days.

    """

from typing import List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from src.database.database import get_db
from src.database.models import User
from src.repository import contacts as contacts_repo
from src.schemas import ContactCreate, ContactOut
from src.repository.auth import require_verified_user, get_current_user
from src.utils.limiter import limiter

router = APIRouter()


@router.post("/contacts/", response_model=ContactOut)
@limiter.limit("5/minute") 
def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    """
    Create a new contact for the current user.

    :param request: The HTTP request object.
    :type request: Request
    :param contact: The data for the new contact.
    :type contact: ContactCreate
    :param db: Database session used to create the contact.
    :type db: Session
    :param current_user: The currently authenticated and verified user.
    :type current_user: User
    :return: The created contact.
    :rtype: ContactOut
    
    """
    return contacts_repo.create_contact(db=db, contact=contact, user_id=current_user.id)

@router.get("/contacts/", response_model = List[ContactOut])
@limiter.limit("5/minute") 
def read_contacts(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    """
    Retrieve all contacts for the current user, with optional pagination.

    :param request: The HTTP request object.
    :type request: Request
    :param skip: The number of records to skip (default: 0).
    :type skip: int
    :param limit: The maximum number of records to return (default: 100).
    :type limit: int
    :param db: Database session used to query the contacts.
    :type db: Session
    :param current_user: The currently authenticated and verified user.
    :type current_user: User
    :return: A list of contacts.
    :rtype: List[ContactOut]
    
    """
    contacts = contacts_repo.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@router.get("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def read_contact(
    request: Request,
    contact_id:int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    """
    Retrieve details of a specific contact.

    :param request: The HTTP request object.
    :type request: Request
    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: Database session used to query the contact.
    :type db: Session
    :param current_user: The currently authenticated and verified user.
    :type current_user: User
    :return: The requested contact.
    :rtype: ContactOut
    :raises HTTPException: If the contact is not found.
    
    """
    contact = contacts_repo.get_contact(db, user_id=current_user.id, contact_id=contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return contact

@router.put("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def update_contact(
    request: Request,
    contact_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    """
    Update a specific contact's details.

    :param request: The HTTP request object.
    :type request: Request
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param contact: The updated contact data.
    :type contact: ContactCreate
    :param db: Database session used to update the contact.
    :type db: Session
    :param current_user: The currently authenticated and verified user.
    :type current_user: User
    :return: The updated contact.
    :rtype: ContactOut
    :raises HTTPException: If the contact is not found.
    
    """
    updated_contact = contacts_repo.update_contact(db, user_id=current_user.id, contact_id=contact_id, contact=contact)
    if updated_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = "Contact not found",
                            )
    return updated_contact

@router.delete("/contacts/{contact_id}", response_model=ContactOut)
@limiter.limit("5/minute") 
def delete_contact(
    request: Request,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    """
    Delete a specific contact.

    :param request: The HTTP request object.
    :type request: Request
    :param contact_id: The ID of the contact to delete.
    :type contact_id: int
    :param db: Database session used to delete the contact.
    :type db: Session
    :param current_user: The currently authenticated and verified user.
    :type current_user: User
    :return: The deleted contact.
    :rtype: ContactOut
    :raises HTTPException: If the contact is not found.
    
    """
    deleted_contact = contacts_repo.delete_contact(db, user_id=current_user.id, contact_id=contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return deleted_contact

@router.get("/contacts/search", response_model=List[ContactOut])
@limiter.limit("10/minute") 
def search_contact(
    request: Request,
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search contacts by a query string.

    :param request: The HTTP request object.
    :type request: Request
    :param query: The search string to filter contacts.
    :type query: str
    :param db: Database session used to search contacts.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A list of contacts matching the search query.
    :rtype: List[ContactOut]
    
    """
    contacts = contacts_repo.search_contacts(db, user_id=current_user.id, query=query)
    return contacts

@router.get("/contacts/upcoming-birthdays", response_model=List[ContactOut])
@limiter.limit("2/minute") 
def get_upcoming_birthdays(
    request: Request,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve contacts with upcoming birthdays within the specified number of days.

    :param request: The HTTP request object.
    :type request: Request
    :param days: The number of days to look ahead for upcoming birthdays (default: 7).
    :type days: int
    :param db: Database session used to query contacts.
    :type db: Session
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[ContactOut]
    
    """
    today = date.today()
    end_date = today + timedelta(days=days)
    contacts = contacts_repo.get_upcoming_birthdays(db, user_id=current_user.id, start_date=today, end_date=end_date)
    return contacts