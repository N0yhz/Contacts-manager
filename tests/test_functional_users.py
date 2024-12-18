import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from main import app
from src.database.models import Base, User
from src.database.database import get_db
from src.repository import auth as auth_repo

from src.services.email import send_verification_email
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

test_user = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture(scope="module", autouse=True)
async def init_models_wrap():
    async def init_models(): 
        try: 
            async with engine.begin() as conn: 
                await conn.run_sync(Base.metadata.drop_all) 
                await conn.run_sync(Base.metadata.create_all) 
            async with TestingSessionLocal() as session: 
                hash_password = auth_repo.get_password_hash(test_user["password"]) 
                current_user = User(username=test_user["username"], email=test_user["email"], hashed_password=hash_password, is_verified=True)
                session.add(current_user) 
                await session.commit() 
                
                result = await session.execute(text("SELECT * FROM users"))
                users = result.fetchall() 
                print(f"Users in DB: {users}") # Debugging: print users to confirm insertion 
        except Exception as e:
            print(f"An error occurred: {e}") 
    await init_models()

@pytest.fixture(scope="module")
def client():
    # Dependency override
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

user_data = {"username": "testuser2", "email": "test2@example.com", "password": "1234567890"}

def test_create_user(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    print("User Data:", user_data)
    print("Mock Email Function:", mock_send_email)

    response = client.post("/api/auth/register", json=user_data)

    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id " in data, "UserID not set in response"
    print("User ID:", data["id"])
    mock_send_email.assert_called_once()