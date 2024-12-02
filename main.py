import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.routes import auth, contacts
from src.database.database import get_db
from src.schemas import UserModel, UserResponse
from src.repository import users as repository_users

app = FastAPI()

app.include_router(auth.router, prefix = "/api")
app.include_router(contacts.router, prefix = "/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to Contact Manager"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)