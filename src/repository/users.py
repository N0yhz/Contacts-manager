from typing import Optional
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel, UserDb



def get_user_by_email(db: Session, email: str) -> Optional[UserDb]:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return UserDb.from_orm(user)
    return None

def create_user(db: Session, body: UserModel) -> UserDb:
    new_user = User(email=body.email, username=body.username, hashed_password=body.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserDb.from_orm(new_user)


async def update_token(user: User, token: Optional[str], db: Session) -> None:
    db_user = db.query(User).filter(User.id == user.id).first()
    db_user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    user = db.query(User).filter(User.email == email).first()
    user.confirmed = True
    db.commit()
