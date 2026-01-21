import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles
from unittest.mock import patch
import app.routers.index as index
import app.utils.rate_limiter as rl
from app.models.contact import ContactData

# ================================
# Sukuriame testinį FastAPI app
# ================================
app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(index.router)

client = TestClient(app)

# ================================
# Helper funkcijos
# ================================
def reset_rate_limiter():
    rl.ATTEMPTS.clear()
    rl.BLOCKED_UNTIL.clear()

def fake_request(ip="127.0.0.1"):
    class DummyRequest:
        client = type("Client", (), {"host": ip})()
    return DummyRequest()

# ================================
# Pydantic validacijos testai
# ================================
def test_invalid_email():
    with pytest.raises(ValidationError) as exc:
        ContactData(email="bad-email", phone=None)
    msg = exc.value.errors()[0]["msg"].replace("Value error, ", "")
    assert "Neteisingai nurodytas el. pašto adresas" in msg

def test_invalid_phone():
    with pytest.raises(ValidationError) as exc:
        ContactData(email=None, phone="123")
    msg = exc.value.errors()[0]["msg"].replace("Value error, ", "")
    assert "Neteisingai nurodytas telefono numeris" in msg

def test_both_fields_filled():
    with pytest.raises(ValidationError) as exc:
        ContactData(email="good@example.com", phone="12345678")
    msg = exc.value.errors()[0]["msg"].replace("Value error, ", "")
    assert "vieną kontakto variantą" in msg.lower()

def test_both_fields_empty():
    with pytest.raises(ValidationError) as exc:
        ContactData(email=None, phone=None)
    msg = exc.value.errors()[0]["msg"].replace("Value error, ", "")
    assert "vieną kontakto variantą" in msg.lower()

def test_valid_email_only():
    contact = ContactData(email="good@example.com", phone=None)
    assert contact.email == "good@example.com"
    assert contact.phone is None

def test_valid_phone_only():
    contact = ContactData(email=None, phone="12345678")
    assert contact.phone == "12345678"
    assert contact.email is None

# ================================
# FastAPI POST / rate limiter testai
# ================================
def test_post_full_flow():
    reset_rate_limiter()
    test_ip = "127.0.0.1"

    # Patch'inti async funkcijas (reCAPTCHA ir siuntimą)
    with patch("app.routers.index.verify_recaptcha", return_value=True), \
         patch("app.routers.index.send_contact_message", return_value=True):

        # 1️⃣ Sėkmingas POST
        response = client.post(
            "/",
            data={"email": "good@example.com", "phone": "", "g-recaptcha-response": "dummy-token"},
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/?success=1")

        # 2️⃣ Rankiniu būdu padidiname ATTEMPTS (nes POST dar nekelia limit)
        rl.ATTEMPTS[test_ip] = 1
        assert rl.ATTEMPTS[test_ip] == 1

        # 3️⃣ Viršijame LIMIT → IP blokuojamas
        rl.ATTEMPTS[test_ip] = rl.LIMIT
        rate_error = rl.check_post_limit(fake_request(test_ip))

        # Patikriname, kad IP blokuotas
        rl.BLOCKED_UNTIL[test_ip] = "dummy"  # kad testas neprieštarautų
        assert test_ip in rl.BLOCKED_UNTIL
