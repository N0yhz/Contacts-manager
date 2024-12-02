from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

# Contacts
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    owner_id: int
    class Config:
        orm_mode = True


# User
class UserModel(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserDb(UserModel):
    id: int
    username: str
    is_verified: bool
    avatar_url: Optional[str] = None
    refresh_token: Optional[str] = None

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"



# Token
class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# Email
class RequestEmail(BaseModel):
    email: EmailStr