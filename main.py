from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi.responses import JSONResponse
import logging

import crud, models, schemas
from database import engine, get_db
from auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, Token
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    if isinstance(exc, SQLAlchemyError):
        logger.error(f"SQLAlchemy error: {exc}", exc_info=True)
    return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred while querying the database. Please try again later."}
        )

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.post("/contacts/", response_model=schemas.Contact, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        logger.info(f"Received request to create contact: {contact.dict()}")
        logger.info(f"Current user: {current_user.id}")
        result = crud.create_contact(db=db, contact=contact, user_id=current_user.id)
        logger.info(f"Contact created successfully: {result.__dict__}")
        return result
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}", exc_info=True)
        raise

@app.get("/contacts/", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    contacts = crud.get_contacts(db, skip=skip, limit=limit)
    return contacts

@app.get("/contacts/{contact_id}", response_model=schemas.Contact)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.get_contact(db, user_id=current_user.id, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.put("/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact(
    contact_id: int,
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.update_contact(db, user_id=current_user.id, contact_id=contact_id, contact=contact)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contacts/{contact_id}", response_model=schemas.Contact)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.delete_contact(db, user_id=current_user.id, contact_id=contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.get("/contacts/search/", response_model=List[schemas.Contact])
def search_contacts(
    query: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contacts = crud.search_contacts(db, user_id=current_user.id, query=query)
    return contacts

@app.get("/contacts/upcoming_birthdays/", response_model=List[schemas.Contact])
def get_upcoming_birthdays(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contacts = crud.get_upcoming_birthdays(db, user_id=current_user.id)
    return contacts

@app.get("/")
async def root():
    return {"message": "Welcome to the Contact API"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)