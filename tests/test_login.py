from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import pytest

from app.main import app

client = TestClient(app)


def test_login_page_get():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Prisijungimas" in response.text


def test_login_invalid_id():
    data = {
        "login_id": "123",  # per trumpas, turi būti 6 skaičiai
        "password": "SomePassword123!",
        "submit_login": "Prisijungti"
    }
    response = client.post("/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    # Tikrinam fragmentą, be p tagų
    assert "Prisijungimo ID turi būti 6 skaičiai" in response.text


def test_login_invalid_password():
    data = {
        "login_id": "654321",
        "password": "wrongpassword",
        "submit_login": "Prisijungti"
    }

    # Patch verify_password kad visada grąžintų False
    with patch("app.routers.login.verify_password", new=AsyncMock(return_value=False)):
        response = client.post("/login", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert "Neteisingas prisijungimo ID arba slaptažodis" in response.text


def test_login_success():
    data = {
        "login_id": "654321",
        "password": "CorrectPass123!",
        "submit_login": "Prisijungti"
    }

    # Patch verify_password kad visada grąžintų True
    with patch("app.routers.login.verify_password", new=AsyncMock(return_value=True)):
        response = client.post("/login", data=data, follow_redirects=True)

    assert response.status_code == 200
    # Patikrinam, kad puslapyje yra fragmentas, rodomas sėkmingam login
    assert "Sėkmingai prisijungta" in response.text


def test_registration_success():
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "StrongPass123!",
        "g-recaptcha-response": "dummy",
        "submit_register": "Registruotis"
    }

    # Patch async funkcijas, kad nereikėtų realaus reCAPTCHA ar email
    with patch("app.routers.login.verify_recaptcha", new=AsyncMock(return_value=True)), \
            patch("app.routers.login.send_registration_confirmation_email", new=AsyncMock(return_value=None)), \
            patch("app.routers.login.create_user_in_db", new=AsyncMock(return_value=True)):
        response = client.post("/login", data=data, follow_redirects=True)

    assert response.status_code == 200
    assert "Jūsų paskyra sukurta" in response.text
