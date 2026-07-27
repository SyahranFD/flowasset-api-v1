from starlette.testclient import TestClient


# ─────────────────────────────────────────────────────────────
# POST /api/v1/auth/register
# ─────────────────────────────────────────────────────────────

def test_register_success(client: TestClient):
    """Happy path: register a new user, should return 201 with user data."""
    response = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "securepassword",
        "full_name": "Alice Smith",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Smith"
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    """Registering the same email twice should return 400."""
    payload = {
        "email": "dup@example.com",
        "password": "securepassword",
        "full_name": "Duplicate User",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_missing_fields(client: TestClient):
    """Missing full_name should return 422 validation error."""
    response = client.post("/api/v1/auth/register", json={
        "email": "noname@example.com",
        "password": "securepassword",
    })
    assert response.status_code == 422


def test_register_invalid_email(client: TestClient):
    """Non-email string should return 422 validation error."""
    response = client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "securepassword",
        "full_name": "Bad Email",
    })
    assert response.status_code == 422


def test_register_short_password(client: TestClient):
    """Password under 8 characters should return 422."""
    response = client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "abc",
        "full_name": "Short Pass",
    })
    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────
# POST /api/v1/auth/login
# ─────────────────────────────────────────────────────────────

def test_login_success(client: TestClient):
    """Happy path: login should return access_token and refresh_token."""
    client.post("/api/v1/auth/register", json={
        "email": "bob@example.com",
        "password": "bobpassword",
        "full_name": "Bob Jones",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "bob@example.com",
        "password": "bobpassword",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """Wrong password should return 401."""
    client.post("/api/v1/auth/register", json={
        "email": "charlie@example.com",
        "password": "rightpassword",
        "full_name": "Charlie",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "charlie@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_nonexistent_email(client: TestClient):
    """Login with email that doesn't exist should return 401."""
    response = client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "anypassword",
    })
    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────
# POST /api/v1/auth/refresh
# ─────────────────────────────────────────────────────────────

def test_refresh_token_success(client: TestClient):
    """Valid refresh token should return a new access token."""
    client.post("/api/v1/auth/register", json={
        "email": "diana@example.com",
        "password": "dianapassword",
        "full_name": "Diana",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "diana@example.com",
        "password": "dianapassword",
    })
    refresh_token = login_res.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client: TestClient):
    """Garbage refresh token should return 401."""
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "this.is.not.a.valid.token",
    })
    assert response.status_code == 401


def test_refresh_using_access_token_fails(client: TestClient):
    """Access token must not be accepted by /refresh endpoint."""
    client.post("/api/v1/auth/register", json={
        "email": "eve@example.com",
        "password": "evepassword",
        "full_name": "Eve",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "eve@example.com",
        "password": "evepassword",
    })
    access_token = login_res.json()["access_token"]

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": access_token,
    })
    assert response.status_code == 401


# ─────────────────────────────────────────────────────────────
# GET /api/v1/auth/me
# ─────────────────────────────────────────────────────────────

def test_get_me_success(client: TestClient, auth_headers: dict):
    """Authenticated request should return current user data."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@flowasset.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data


def test_get_me_no_token(client: TestClient):
    """No Authorization header: HTTPBearer returns 403."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_get_me_invalid_token(client: TestClient):
    """Invalid token should return 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401
