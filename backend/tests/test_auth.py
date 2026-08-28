import pytest
from fastapi import status
from backend.app.core.security import verify_password, get_password_hash

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

def test_existing_bcrypt_password_hash_verification():
    """Verify that existing legacy bcrypt hashes ($2b$ and $2a$) remain 100% verifiable."""
    # Pre-existing legacy bcrypt hash for "hod_csm_secure_2026"
    legacy_hash_2b = "$2b$12$e1MKzOt7Atd3jAhbSLDxheaIaeYO4dAUDh7.Y2KkOAlb9DUa5uo.W"
    assert verify_password("hod_csm_secure_2026", legacy_hash_2b) is True
    assert verify_password("wrong_password", legacy_hash_2b) is False

    # Newly generated hash
    new_hash = get_password_hash("test_password_xyz_2026")
    assert verify_password("test_password_xyz_2026", new_hash) is True
    assert verify_password("wrong_password", new_hash) is False

def test_password_longer_than_72_bytes_handling(client):
    """Verify that passwords > 72 bytes do NOT crash with HTTP 500 / ValueError and return HTTP 401."""
    long_password = "a" * 150
    # Direct security function verification
    legacy_hash = "$2b$12$e1MKzOt7Atd3jAhbSLDxheaIaeYO4dAUDh7.Y2KkOAlb9DUa5uo.W"
    assert verify_password(long_password, legacy_hash) is False

    # API endpoint verification
    response = client.post("/api/auth/login", json={
        "username": "hod.csm",
        "password": long_password
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

def test_protected_endpoint_with_valid_jwt(client, auth_headers):
    response = client.get("/api/dashboard/overview", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

def test_get_current_hod_profile(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "hod.csm"
    assert data["role"] == "HOD"
    assert data["department"] == "CSM"
