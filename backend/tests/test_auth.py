
import uuid


BASE_URL = "/api/auth"


# ==========================================
# HELPER: GENERATE UNIQUE USER DATA
# ==========================================

def user_data():

    unique_id = uuid.uuid4().hex[:8]

    return {
        "name": "Test Donor",
        "email": f"test_{unique_id}@gmail.com",
        "password": "TestPassword123",
        "phone": "9876543210",
        "role": "donor"
    }


# ==========================================
# HELPER: REGISTER USER
# ==========================================

def register_user(client):

    data = user_data()

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 201

    return data


# ==========================================
# HELPER: LOGIN AND GET ACCESS TOKEN
# ==========================================

def get_access_token(client, data):

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "email": data["email"],
            "password": data["password"]
        }
    )

    assert response.status_code == 200

    result = response.get_json()

    def find_token(value):

        if isinstance(value, dict):

            if "access_token" in value:
                return value["access_token"]

            for item in value.values():
                token = find_token(item)

                if token:
                    return token

        return None

    token = find_token(result)

    assert token is not None, "Access token not found"

    return token


# ==========================================
# 1. SUCCESSFUL REGISTRATION
# ==========================================

def test_register_user(client):

    data = user_data()

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 201

    result = response.get_json()

    assert result["message"] == "Registration successful"
    assert result["data"]["user"]["email"] == data["email"]


# ==========================================
# 2. DUPLICATE EMAIL REGISTRATION
# ==========================================

def test_duplicate_registration(client):

    data = register_user(client)

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 409


# ==========================================
# 3. REGISTRATION WITH INVALID EMAIL
# ==========================================

def test_invalid_email_registration(client):

    data = user_data()
    data["email"] = "invalid-email"

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 400


# ==========================================
# 4. REGISTRATION WITH WEAK PASSWORD
# ==========================================

def test_weak_password_registration(client):

    data = user_data()
    data["password"] = "123"

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 400


# ==========================================
# 5. REGISTRATION WITH INVALID ROLE
# ==========================================

def test_invalid_role_registration(client):

    data = user_data()
    data["role"] = "admin"

    response = client.post(
        f"{BASE_URL}/register",
        json=data
    )

    assert response.status_code == 400


# ==========================================
# 6. REGISTRATION WITH MISSING FIELDS
# ==========================================

def test_missing_registration_fields(client):

    response = client.post(
        f"{BASE_URL}/register",
        json={
            "name": "Test Donor",
            "email": "missing@gmail.com"
        }
    )

    assert response.status_code == 400


# ==========================================
# 7. REGISTRATION WITH INVALID JSON
# ==========================================

def test_invalid_registration_body(client):

    response = client.post(
        f"{BASE_URL}/register",
        data="invalid json",
        content_type="application/json"
    )

    assert response.status_code == 400


# ==========================================
# 8. SUCCESSFUL LOGIN
# ==========================================

def test_login_user(client):

    data = register_user(client)

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "email": data["email"],
            "password": data["password"]
        }
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["message"] == "Login successful"


# ==========================================
# 9. LOGIN WITH INCORRECT PASSWORD
# ==========================================

def test_login_wrong_password(client):

    data = register_user(client)

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "email": data["email"],
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401


# ==========================================
# 10. LOGIN WITH UNKNOWN EMAIL
# ==========================================

def test_login_unknown_email(client):

    response = client.post(
        f"{BASE_URL}/login",
        json={
            "email": "unknown@gmail.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 401


# ==========================================
# 11. GET CURRENT USER DETAILS
# ==========================================

def test_get_current_user(client):

    data = register_user(client)

    token = get_access_token(client, data)

    response = client.get(
        f"{BASE_URL}/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["message"] == "User details retrieved successfully"
    assert result["data"]["user"]["email"] == data["email"]


# ==========================================
# 12. ACCESS CURRENT USER WITHOUT TOKEN
# ==========================================

def test_get_current_user_without_token(client):

    response = client.get(
        f"{BASE_URL}/me"
    )

    assert response.status_code == 401


# ==========================================
# 13. SUCCESSFUL LOGOUT
# ==========================================

def test_logout_user(client):

    data = register_user(client)

    token = get_access_token(client, data)

    response = client.post(
        f"{BASE_URL}/logout",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["message"] == "Logout successful. Token has been revoked"


# ==========================================
# 14. ACCESS AFTER LOGOUT
# ==========================================

def test_access_after_logout(client):

    data = register_user(client)

    token = get_access_token(client, data)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    logout_response = client.post(
        f"{BASE_URL}/logout",
        headers=headers
    )

    assert logout_response.status_code == 200

    response = client.get(
        f"{BASE_URL}/me",
        headers=headers
    )

    assert response.status_code == 401
