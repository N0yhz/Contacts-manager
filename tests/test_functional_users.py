import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.database import get_db
from src.database.models import Base
from src.repository import auth as auth_repo
from src.repository import users as users_repo

SQLALCHEMY_DATABASE_URL = "postgresql://n0yhz:module11@db:7654/test_db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # use a connection pool for testing to speed up tests
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def session():

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def test_client(session):
    def override_get_db():
        try: 
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

@pytest.fixture(scope="function")
def user():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword",}

def test_create_user(client, user):
    response =  client.post("/api/auth/register", json=user)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user["username"]
    assert data["email"] == user["email"]
    assert "id " in data["user"]

def test_repeat_create_user(client, user):
    response =  client.post("/api/auth/register", json=user)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Account already registered"

def test_login_user(client, user):
    response =  client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_type" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, user):
    response = client.post("/api/auth/login", data={"username": user["email"], "password": "wrongpassword"})
    assert response.status_code == 401
    data = response.json()["detail"] == "Invalid email or password"

def test_login_wrong_email(client, user):
    response = client.post("/api/auth/login", data={"username": "wrongemail@example.com", "password": user["password"]})
    assert response.status_code == 401
    data = response.json()["detail"] == "Invalid email or password"

def test_get_current_user(client, user):
    login_response = client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user["email"]

def test_update_user_avatar(client, user):
    login_response = client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    avatar_url = "https://i.pinimg.com/736x/cc/ba/de/ccbade17e6bb74faccd8ce88659018b9.jpg"
    response = client.patch("/api/users/avatar", json={"avatr_url": avatar_url}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] == avatar_url

def test_request_email_verification(client, user, mocker):
    mock_send_email = mocker.patch('src.services.email.send_verification_email')

    response = client.post("/api/auth/resend-verification", json={"email": user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Verification email sent"
    mock_send_email.assert_called_once()

def test_confirm_email(client, mocker):

    mocker.patch.object(auth_repo, "verify_token", return_value="test@example.com")
    mocker.patch.object(users_repo, "verify_user", return_value = True)

    response = client.get("/api/auth/verify/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified"

def test_refresh_token(client, user):
    login_response = client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/api/auth/token", json={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_request_password_reset(client, user, mocker):
    mock_send_email = mocker.patch('src.services.email.send_password_reset_email')

    response = client.post("/api/auth/forgot-password", json={"email": user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Reset password email sent"
    mock_send_email.assert_called_once()

def test_reset_password(client, mocker):

    mocker.patch.object(auth_repo, "verify_token", return_value="test@example.com")
    mocker.patch.object(users_repo, "update_password", return_value = True)

    response = client.post("/api/auth/reset-password/{token}", json={"new_password": "newpassword123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"