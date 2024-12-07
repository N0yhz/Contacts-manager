import uvicorn
from src.routers import auth, contacts
from src.limiter import limiter

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
    return {"message": "Welcome to Contact Manager"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)