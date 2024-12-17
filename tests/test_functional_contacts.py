import os, sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.confests import client

@pytest.fixture(scope="module")
def test_user():
    user_data = {"username": "testuser", "email": "testuser@example.com", "password": "testpassword123"}
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    new_user = response.json()
    return new_user

@pytest.fixture(scope="module")
def access_token(test_user):
    response = client.post("/api/auth/token", data={"username": test_user["username"], "password": "testpassword123"})
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]

def test_create_contact(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "Trang",
        "last_name": "Zyonh",
        "email": "trangzyonh@example.com",
        "phone_number": "1234567890",
        "birthday": "2001-01-01",
        "additional_data": "Hello Vietnam"
    }
    response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
    assert response.status_code == 200
    created_contact = response.json()
    assert created_contact["first_name"] == contact_data["first_name"]
    assert created_contact["last_name"] == contact_data["last_name"]
    assert created_contact["email"] == contact_data["email"]
    assert created_contact["phone_number"] == contact_data["phone_number"]
    assert created_contact["birthday"] == contact_data["birthday"]
    assert created_contact["additional_data"] == contact_data["additional_data"]
    assert "id" in created_contact

def test_get_contacts(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/contacts/contacts", headers=headers)
    assert response.status_code == 200
    contacts = response.json()
    assert isinstance(contacts, list)
    assert len(contacts) > 0

def test_get_contact(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "David",
        "last_name": "Doe",
        "email": "david@example.com",
        "phone_number": "1111222340"
    }
    create_response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
    assert create_response.status_code == 201
    created_contact = create_response.json()

    response = client.get(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
    assert response.status_code == 200
    retrieved_contact = response.json()
    assert retrieved_contact== created_contact

def test_update_contact(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "Ana",
        "last_name": "Smith",
        "email": "asmith@example.com",
        "phone_number": "1234567890",
        "birthday": "1990-05-15",
        "additional_data": "string12345"
    }
    create_response = client.post("/api/contacts/contacts/", json=contact_data, headers=headers)
    assert create_response.status_code == 201
    created_contact = create_response.json()

    updated_contact_data = {
        "first_name": "Anastasia",
        "last_name": "Smith",
        "email": "anasmith@example.com",
        "phone_number": "9876543210",
    }
    response = client.put(f"/api/contacts/contacts/{created_contact['id']}", json=updated_contact_data, headers=headers)
    assert response.status_code == 200
    updated_contact = response.json()
    assert updated_contact["first_name"] == updated_contact_data["first_name"]
    assert updated_contact["last_name"] == updated_contact_data["last_name"]
    assert updated_contact["email"] == updated_contact_data["email"]
    assert updated_contact["phone_number"] == updated_contact_data["phone_number"]

def test_delete_contact(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "Trang",
        "last_name": "Zyonh",
        "email": "trangzyonh@example.com",
        "phone_number": "1234567890",
    }
    create_response = client.post("/api/contacts/contacts/", json=contact_data, headers=headers)
    assert create_response.status_code == 201
    created_contact = create_response.json()

    response = client.delete(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
    assert response.status_code == 204

    get_response = client.get(f"/api/contacts/contacts/{created_contact['id']}", headers=headers)
    assert get_response.status_code == 404

def test_create_contact_invalid_email(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "Invalid",
        "last_name": "Email",
        "email": "invalid-email",
        "phone_number": "1234565550",
        "birthday": "2001-01-02",
        "additional_data": "string123"
    }
    response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
    assert response.status_code == 422

def test_create_contact_missing_field(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    contact_data = {
        "first_name": "Missing",
        "last_name": "Field",
        "phone_number": "1234567890",
        "birthday": "2001-01-05",
        "additional_data": "string123"
    }
    response = client.post("/api/contacts/contacts", json=contact_data, headers=headers)
    assert response.status_code == 422