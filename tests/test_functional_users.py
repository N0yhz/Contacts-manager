import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, AsyncMock

pytestmark = pytest.mark.asyncio

def test_create_user(client, user, monkeypatch):
    mock_send_email = AsyncMock()
    monkeypatch.setattr("src.services.email.send_verification_email", mock_send_email)

    response = client.post("/api/auth/register", json=user)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user["username"]
    assert data["email"] == user["email"]
    assert "id " in data
    mock_send_email.assert_called_once()

def test_repeat_create_user(client, user):
    response =  client.post("/api/auth/register", json=user)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Account already registered"

def test_login_user(client, user, monkeypatch):
    mock_verify = Mock(return_value=True)
    monkeypatch.setattr("src.repository.auth.verify_password", mock_verify)

    response =  client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_type" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, user, monkeypatch):
    mock_verify = Mock(return_value=True)
    monkeypatch.setattr("src.repository.auth.verify_password", mock_verify)

    response = client.post("/api/auth/login", data={"username": user["email"], "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_login_wrong_email(client, user):
    response = client.post("/api/auth/login", data={"username": "wrongemail@example.com", "password": user["password"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_get_current_user(client, user, token_header, monkeypatch):
    mock_get_current_user = Mock(return_value=user)
    monkeypatch.setattr("src.repository.auth.get_current_user",mock_get_current_user)

    response = client.get("/api/users/me", headers=token_header)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user["email"]
    assert data["username"] == user["username"]

def test_update_user_avatar(client, user, token_header, monkeypatch):
    mock_get_current_user=Mock(return_value=user)
    monkeypatch.setattr("src.repository.auth.get_current_user", mock_get_current_user)

    avatar_url = "https://i.pinimg.com/736x/cc/ba/de/ccbade17e6bb74faccd8ce88659018b9.jpg"
    response = client.patch("/api/users/avatar", json={"avatr_url": avatar_url}, headers=token_header)
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] == avatar_url

def test_request_email_verification(client, user, monkeypatch):
    mock_send_email = AsyncMock()
    monkeypatch.setattr('src.services.email.send_verification_email', mock_send_email)

    response = client.post("/api/auth/resend-verification", json={"email": user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Verification email sent"
    assert mock_send_email.called

def test_confirm_email(client, monkeypatch):

    mock_verify_token = Mock(return_value="test@example.com")
    monkeypatch.setattr("src.repository.auth.verify_token", mock_verify_token)

    response = client.get("/api/auth/verify/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified"

def test_request_password_reset(client, user, monkeypatch):
    mock_send_email = AsyncMock()
    monkeypatch.setattr('src.services.email.send_password_reset_email', mock_send_email)

    response = client.post("/api/auth/forgot-password", json={"email": user["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == "Reset password email sent"
    mock_send_email.assert_called_once()

def test_reset_password(client, monkeypatch):
    mock_verify_token = Mock(return_value="test@xexample.com")
    monkeypatch.setattr("src.repository.auth.verify_token", mock_verify_token)

    response = client.post("/api/auth/reset-password/{token}", json={"new_password": "newpassword123"})
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"