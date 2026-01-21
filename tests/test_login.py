# LOGIN INVALID PASSWORD
def test_login_invalid_password():
    with patch("app.routers.login.verify_password", return_value=False):
        response = client.post(
            "/login",
            data={"login_id": "123456", "password": "WrongPass", "submit_login": "Prisijungti"},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert "Neteisingas prisijungimo ID arba slaptažodis" in response.text

# LOGIN INVALID ID
def test_login_invalid_id():
    response = client.post(
        "/login",
        data={"login_id": "123", "password": "Test1234", "submit_login": "Prisijungti"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Prisijungimo ID turi būti 6 skaičiai" in response.text

# REGISTRATION SUCCESS
def test_registration_success():
    response = client.post(
        "/login",
        data={
            "first_name": "Jonas",
            "last_name": "Jonaitis",
            "email": "jonas@test.com",
            "password": "Test1234A",
            "g-recaptcha-response": "dummy",
            "submit_register": "Registruotis"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Jūsų paskyra sukurta" in response.text
