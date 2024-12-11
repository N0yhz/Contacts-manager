"""
Main Application Module

This module sets up and runs the main FastAPI application.

Dependencies:
    - uvicorn: For running the ASGI server
    - fastapi: For creating the API
    - fastapi.templating: For Jinja2 templates
    - fastapi.middleware.cors: For CORS middleware
    - slowapi: For rate limiting

Routers:
    - auth: Authentication routes
    - contacts: Contact management routes

Configuration:
    - Sets up CORS middleware
    - Configures rate limiting
    - Sets up Jinja2 templates

Routes:
    - GET /: Root endpoint returning a welcome message

Usage:
    Run this file to start the FastAPI application server.

"""

import uvicorn
from src.routers import auth, contacts
from src.utils.limiter import limiter
from src.database.database import Base, engine

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="src/services/templates")
templates_2 = Jinja2Templates(directory="src/templates")

app.include_router(auth.router, prefix="/api/auth", tags=["auhtentication"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def read_root():
    """
    Root endpoint that returns a welcome message.

    :return: A dictionary containing a welcome message
    :rtype: dict
    
    """
    return {"message": "Welcome to Contact Manager"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)