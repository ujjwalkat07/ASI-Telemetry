"""Test user name and password update endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_update_name_and_password():
    # 1. Sign up new test user
    email = "update_test_user@example.com"
    orig_pwd = "OriginalPassword123!"
    signup_payload = {
        "name": "Original Name",
        "email": email,
        "password": orig_pwd,
    }
    resp = client.post("/api/auth/signup", json=signup_payload)
    assert resp.status_code == 201
    auth_data = resp.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Update name only
    resp = client.put(
        "/api/auth/profile",
        headers=headers,
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 200
    user_data = resp.json()
    assert user_data["name"] == "Updated Name"
    assert user_data["email"] == email

    # Verify /api/auth/me returns the updated name
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["name"] == "Updated Name"

    # 3. Update password with incorrect current password -> should fail (400)
    resp = client.put(
        "/api/auth/profile",
        headers=headers,
        json={
            "current_password": "WrongPassword!",
            "new_password": "NewSecretPassword456!",
        },
    )
    assert resp.status_code == 400
    assert "Current password is incorrect" in resp.json()["detail"]

    # 4. Update password with correct current password -> should succeed
    resp = client.put(
        "/api/auth/profile",
        headers=headers,
        json={
            "current_password": orig_pwd,
            "new_password": "NewSecretPassword456!",
        },
    )
    assert resp.status_code == 200

    # 5. Verify old password cannot log in anymore
    old_login = client.post("/api/auth/login", json={"email": email, "password": orig_pwd})
    assert old_login.status_code == 401

    # 6. Verify new password can log in successfully
    new_login = client.post("/api/auth/login", json={"email": email, "password": "NewSecretPassword456!"})
    assert new_login.status_code == 200
    assert new_login.json()["user"]["name"] == "Updated Name"


def test_update_empty_payload_fails():
    email = "empty_payload_user@example.com"
    pwd = "OriginalPassword123!"
    resp = client.post("/api/auth/signup", json={"name": "Empty Test", "email": email, "password": pwd})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/api/auth/profile", headers=headers, json={})
    assert resp.status_code == 400
