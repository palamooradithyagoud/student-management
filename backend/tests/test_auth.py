import pytest
from fastapi import status

def test_hod_valid_login(client):
    response = client.post("/api/auth/login", json={
        "username": "hod.csm",
        "password": "hod_csm_secure_2026"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "username": "hod.csm",
        "password": "wrong_password_123"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()

def test_login_invalid_username(client):
    response = client.post("/api/auth/login", json={
        "username": "admin.cse",
        "password": "hod_csm_secure_2026"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_protected_endpoint_without_token(client):
    response = client.get("/api/dashboard/overview")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_protected_endpoint_with_invalid_token(client):
    response = client.get(
        "/api/dashboard/overview",
        headers={"Authorization": "Bearer invalid_fake_token_xyz"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_hod_profile(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "hod.csm"
    assert data["role"] == "HOD"
    assert data["department"] == "CSM"
