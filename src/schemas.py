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

class ContactOut(ContactBase):
    id: int
    owner_id: int
    class Config:
        orm_mode = True

# User
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_verified: bool
    avatar_url: Optional[str] = None
    class Config:
        orm_mode = True

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Password

class PasswordReset(BaseModel):
    email: EmailStr

class NewPassword(BaseModel):
    new_password: str


class EmailSchema(BaseModel):
    email: EmailStr