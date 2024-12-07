from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from src.database.database import get_db
from src.database.models import User
from src.repository import contacts as contacts_repo
from src.schemas import ContactCreate, ContactOut
from src.repository.auth import require_verified_user

router = APIRouter()

@router.post("/contacts/", response_model=ContactOut)
def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    return contacts_repo.create_contact(db=db, contact=contact, user_id=current_user.id)

@router.get("/contacts/", response_model = List[ContactOut])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contacts = contacts_repo.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)
    return contacts

@router.get("/contacts/{contact_id}", response_model=ContactOut)
def read_contact(
    contact_id:int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contact = contacts_repo.get_contact(db, user_id=current_user.id, contact_id=contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return contact

@router.put("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(
    contact_id: int,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    updated_contact = contacts_repo.update_contact(db, user_id=current_user.id, contact_id=contact_id, contact=contact)
    if updated_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail = "Contact not found",
                            )
    return updated_contact

@router.delete("/contacts/{contact_id}", response_model=ContactOut)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user),
):
    deleted_contact = contacts_repo.delete_contact(db, user_id=current_user.id, contact_id=contact_id)
    if deleted_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = "Contact not found",
                            )
    return deleted_contact

@router.get("/contacts/search", response_model=List[ContactOut])
def search_contact(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contacts = contacts_repo.search_contacts(db, user_id=current_user.id, query=query)
    return contacts

@router.get("/contacts/upcoming-birthdays", response_model=List[ContactOut])
def get_upcoming_birthdays(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verified_user)
):
    contacts = contacts_repo.get_upcoming_birthdays(db, user_id=current_user.id)
    return contacts