import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from models import db, User, UserProfile


@pytest.fixture
def app():
    app = create_app("testing")

    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(email="admin@test.com", role="admin")
        admin.set_password("Password123")

        client = User(email="client@test.com", role="client")
        client.set_password("Password123")

        db.session.add_all([admin, client])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_headers(app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        token = create_access_token(identity=str(admin.id))
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client_headers(app):
    with app.app_context():
        user = User.query.filter_by(email="client@test.com").first()
        token = create_access_token(identity=str(user.id))
        return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_api_root(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "admin" in data["data"]["endpoints"]


def test_admin_users_requires_token(client):
    response = client.get("/api/admin/users")

    assert response.status_code == 401


def test_admin_users_rejects_non_admin(client, client_headers):
    response = client.get("/api/admin/users", headers=client_headers)

    assert response.status_code == 403
    assert response.get_json()["success"] is False


def test_admin_can_get_users(client, admin_headers):
    response = client.get("/api/admin/users", headers=admin_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "users" in data["data"]


def test_admin_create_user_missing_email_password(client, admin_headers):
    response = client.post("/api/admin/users", json={}, headers=admin_headers)

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_admin_create_user_invalid_email(client, admin_headers):
    response = client.post(
        "/api/admin/users",
        json={
            "email": "bad-email",
            "password": "Password123",
            "role": "client"
        },
        headers=admin_headers
    )

    assert response.status_code == 400


def test_admin_create_user_success(client, admin_headers):
    response = client.post(
        "/api/admin/users",
        json={
            "email": "newuser@test.com",
            "password": "Password123",
            "role": "client",
            "first_name": "New",
            "last_name": "User"
        },
        headers=admin_headers
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "newuser@test.com"


def test_admin_update_missing_user(client, admin_headers):
    response = client.put(
        "/api/admin/users/99999",
        json={"first_name": "Ghost"},
        headers=admin_headers
    )

    assert response.status_code == 404


def test_admin_update_user_success(client, admin_headers, app):
    with app.app_context():
        user = User.query.filter_by(email="client@test.com").first()
        user_id = user.id

    response = client.put(
        f"/api/admin/users/{user_id}",
        json={
            "first_name": "Updated",
            "last_name": "Client",
            "role": "both"
        },
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["role"] == "both"


def test_admin_cannot_delete_self(client, admin_headers, app):
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        admin_id = admin.id

    response = client.delete(
        f"/api/admin/users/{admin_id}",
        headers=admin_headers
    )

    assert response.status_code == 400


def test_admin_stats(client, admin_headers):
    response = client.get("/api/admin/stats", headers=admin_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "total_users" in data["data"]