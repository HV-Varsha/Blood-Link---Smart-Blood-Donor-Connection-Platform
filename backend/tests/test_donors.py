import uuid

import pytest


BASE_URL = "/api/donors"


# ==========================================
# HELPER: REGISTER AND LOGIN DONOR
# ==========================================

def create_donor_user(client):

    unique_id = uuid.uuid4().hex[:8]

    user_data = {
        "name": "Test Donor",
        "email": f"donor_{unique_id}@gmail.com",
        "password": "TestPassword123",
        "phone": "9876543210",
        "role": "donor"
    }

    register_response = client.post(
        "/api/auth/register",
        json=user_data
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"]
        }
    )

    assert login_response.status_code == 200

    response_data = login_response.get_json()

    # Find access token in the response
    def find_token(data):
        if isinstance(data, dict):
            if "access_token" in data:
                return data["access_token"]

            for value in data.values():
                result = find_token(value)
                if result:
                    return result

        return None

    token = find_token(response_data)

    assert token is not None, "Access token not found"

    return {
        "Authorization": f"Bearer {token}"
    }


# ==========================================
# DONOR PROFILE TEST DATA
# ==========================================

def donor_data():

    return {
        "blood_group": "O+",
        "area": "Vijayanagar",
        "city": "Mysuru",
        "age": 23,
        "last_donation_date": "2026-01-15"
    }


# ==========================================
# 1. CREATE DONOR PROFILE
# ==========================================

def test_create_donor_profile(client):

    headers = create_donor_user(client)

    response = client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    assert response.status_code == 201

    result = response.get_json()

    assert result["message"] == "Donor profile created successfully"
    assert result["data"]["donor"]["blood_group"] == "O+"


# ==========================================
# 2. PREVENT DUPLICATE DONOR PROFILE
# ==========================================

def test_duplicate_donor_profile(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    assert response.status_code == 409


# ==========================================
# 3. VIEW OWN DONOR PROFILE
# ==========================================

def test_get_donor_profile(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.get(
        f"{BASE_URL}/profile",
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["data"]["donor"]["area"] == "Vijayanagar"


# ==========================================
# 4. UPDATE DONOR PROFILE
# ==========================================

def test_update_donor_profile(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.put(
        f"{BASE_URL}/profile",
        json={
            "area": "Hebbal",
            "age": 24
        },
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["data"]["donor"]["area"] == "Hebbal"
    assert result["data"]["donor"]["age"] == 24


# ==========================================
# 5. INVALID AGE UPDATE
# ==========================================

def test_update_invalid_age(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.put(
        f"{BASE_URL}/profile",
        json={"age": 15},
        headers=headers
    )

    assert response.status_code == 400


# ==========================================
# 6. UPDATE DONOR AVAILABILITY
# ==========================================

def test_update_availability(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.patch(
        f"{BASE_URL}/profile/availability",
        json={"is_available": False},
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["data"]["is_available"] is False


# ==========================================
# 7. SEARCH AVAILABLE DONORS
# ==========================================

def test_search_donors(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.get(
        f"{BASE_URL}/search",
        query_string={
            "blood_group": "O+",
            "area": "Vijayanagar",
            "city": "Mysuru"
        },
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["data"]["pagination"]["total_donors"] == 1
    assert len(result["data"]["donors"]) == 1


# ==========================================
# 8. SEARCH WITH INVALID BLOOD GROUP
# ==========================================

def test_search_invalid_blood_group(client):

    headers = create_donor_user(client)

    response = client.get(
        f"{BASE_URL}/search",
        query_string={"blood_group": "X+"},
        headers=headers
    )

    assert response.status_code == 400


# ==========================================
# 9. VIEW SINGLE DONOR
# ==========================================

def test_get_single_donor(client):

    headers = create_donor_user(client)

    create_response = client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    donor_id = create_response.get_json()["data"]["donor"]["id"]

    response = client.get(
        f"{BASE_URL}/{donor_id}",
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["data"]["donor"]["id"] == donor_id


# ==========================================
# 10. VIEW NON-EXISTENT DONOR
# ==========================================

def test_get_nonexistent_donor(client):

    headers = create_donor_user(client)

    response = client.get(
        f"{BASE_URL}/99999",
        headers=headers
    )

    assert response.status_code == 404


# ==========================================
# 11. DELETE DONOR PROFILE
# ==========================================

def test_delete_donor_profile(client):

    headers = create_donor_user(client)

    client.post(
        f"{BASE_URL}/profile",
        json=donor_data(),
        headers=headers
    )

    response = client.delete(
        f"{BASE_URL}/profile",
        headers=headers
    )

    assert response.status_code == 200

    result = response.get_json()

    assert result["message"] == "Donor profile deleted successfully"


# ==========================================
# 12. ACCESS WITHOUT TOKEN
# ==========================================

def test_access_profile_without_token(client):

    response = client.get(
        f"{BASE_URL}/profile"
    )

    assert response.status_code == 401