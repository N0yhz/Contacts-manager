import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.models import Base, User
from src.database.database import get_db
from src.repository.auth import auth_service

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

test_user = {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop.all)
                await conn.run_sync(Base.metadata.create.all)
            async with TestingSessionLocal() as session:
                hash_password = auth_service.get_password_hash(test_user["password"])
                current_user = User(**test_user, hashed_pasword=hash_password, is_verified=True)
                session.add(current_user)
                await session.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
    asyncio.run(init_models())


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

@pytest.fixture(scope="function")
def user():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest_asyncio.fixture()
def get_token():
    token = auth_service.create_access_token(data={"sub": test_user["username"]})
    return token

def test_get_contacts(client, get_token):
    with patch.object(auth_service, "r") as mock_redis:
        mock_redis.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response =  client.get("/api/contacts/contacts", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 0


# def test_create_contact(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     contact_data = {
#         "first_name": "Trang",
#         "last_name": "Zyonh",
#         "email": "trangzyonh@example.com",
#         "phone_number": "1234567890",
#         "birthday": "2001-01-01",
#         "additional_data": "Hello Vietnam"
#     }
#     response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
#     assert response.status_code == 200
#     created_contact = response.json()
#     assert created_contact["first_name"] == contact_data["first_name"]
#     assert created_contact["last_name"] == contact_data["last_name"]
#     assert created_contact["email"] == contact_data["email"]
#     assert created_contact["phone_number"] == contact_data["phone_number"]
#     assert created_contact["birthday"] == contact_data["birthday"]
#     assert created_contact["additional_data"] == contact_data["additional_data"]
#     assert "id" in created_contact

# def test_get_contacts(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     response = client.get("/api/contacts/contacts", headers=headers)
#     assert response.status_code == 200
#     contacts = response.json()
#     assert isinstance(contacts, list)
#     assert len(contacts) > 0

# def test_get_contact(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     contact_data = {
#         "first_name": "David",
#         "last_name": "Doe",
#         "email": "david@example.com",
#         "phone_number": "1111222340"
#     }
#     create_response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
#     assert create_response.status_code == 201
#     created_contact = create_response.json()

#     response = client.get(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
#     assert response.status_code == 200
#     retrieved_contact = response.json()
#     assert retrieved_contact== created_contact

# def test_update_contact(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     contact_data = {
#         "first_name": "Ana",
#         "last_name": "Smith",
#         "email": "asmith@example.com",
#         "phone_number": "1234567890",
#         "birthday": "1990-05-15",
#         "additional_data": "string12345"
#     }
#     create_response = client.post("/api/contacts/contacts/", json=contact_data, headers=headers)
#     assert create_response.status_code == 201
#     created_contact = create_response.json()

#     updated_contact_data = {
#         "first_name": "Anastasia",
#         "last_name": "Smith",
#         "email": "anasmith@example.com",
#         "phone_number": "9876543210",
#     }
#     response = client.put(f"/api/contacts/contacts/{created_contact['id']}", json=updated_contact_data, headers=headers)
#     assert response.status_code == 200
#     updated_contact = response.json()
#     assert updated_contact["first_name"] == updated_contact_data["first_name"]
#     assert updated_contact["last_name"] == updated_contact_data["last_name"]
#     assert updated_contact["email"] == updated_contact_data["email"]
#     assert updated_contact["phone_number"] == updated_contact_data["phone_number"]

# def test_delete_contact(access_token):
#     headers = {"Authorization": f"Bearer {access_token}"}
#     contact_data = {
#         "first_name": "Trang",
#         "last_name": "Zyonh",
#         "email": "trangzyonh@example.com",
#         "phone_number": "1234567890",
#     }
#     create_response = client.post("/api/contacts/contacts/", json=contact_data, headers=headers)
#     assert create_response.status_code == 201
#     created_contact = create_response.json()

#     response = client.delete(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
#     assert response.status_code == 204

#     get_response = client.get(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
#     assert get_response.status_code == 404