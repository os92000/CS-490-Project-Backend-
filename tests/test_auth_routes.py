from unittest import mock
from flask_jwt_extended import create_access_token, create_refresh_token


def test_signup_missing_fields(client):
    response = client.post("/api/auth/signup", json={})

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_signup_invalid_email(client):
    response = client.post("/api/auth/signup", json={
        "email": "bad-email",
        "password": "Password123"
    })

    assert response.status_code == 400


def test_signup_weak_password(client):
    response = client.post("/api/auth/signup", json={
        "email": "newuser@test.com",
        "password": "123"
    })

    assert response.status_code == 400


def test_signup_duplicate_email(client):
    fake_existing_user = mock.Mock()

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_existing_user

        response = client.post("/api/auth/signup", json={
            "email": "taken@test.com",
            "password": "Password123"
        })

    assert response.status_code == 409


def test_signup_success(client):
    fake_user = mock.Mock()
    fake_user.id = 1
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "newuser@test.com",
        "role": None
    }

    with mock.patch("routes.auth_routes.User") as mock_user_class, \
         mock.patch("routes.auth_routes.UserProfile"), \
         mock.patch("routes.auth_routes.db.session") as mock_session:

        mock_user_class.query.filter_by.return_value.first.return_value = None
        mock_user_class.return_value = fake_user

        response = client.post("/api/auth/signup", json={
            "email": "newuser@test.com",
            "password": "Password123"
        })

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    mock_session.add.called
    mock_session.commit.assert_called_once()


def test_login_missing_fields(client):
    response = client.post("/api/auth/login", json={})

    assert response.status_code == 400


def test_login_invalid_credentials_no_user(client):
    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = None

        response = client.post("/api/auth/login", json={
            "email": "fake@test.com",
            "password": "Password123"
        })

    assert response.status_code == 401


def test_login_invalid_password(client):
    fake_user = mock.Mock()
    fake_user.check_password.return_value = False

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user

        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "WrongPassword"
        })

    assert response.status_code == 401


def test_login_disabled_account(client):
    fake_user = mock.Mock()
    fake_user.check_password.return_value = True
    fake_user.status = "disabled"

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user

        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "Password123"
        })

    assert response.status_code == 403


def test_login_success(client):
    fake_user = mock.Mock()
    fake_user.id = 1
    fake_user.status = "active"
    fake_user.check_password.return_value = True
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "role": "client"
    }

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user

        response = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "Password123"
        })

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_logout_requires_token(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 401


def test_logout_success(client, app):
    with app.app_context():
        token = create_access_token(identity="1")

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_refresh_success(client, app):
    with app.app_context():
        refresh_token = create_refresh_token(identity="1")

    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 200
    assert "access_token" in response.get_json()["data"]


def test_me_requires_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_user_not_found(client, app):
    with app.app_context():
        token = create_access_token(identity="999")

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.get.return_value = None

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 404


def test_me_success(client, app):
    with app.app_context():
        token = create_access_token(identity="1")

    fake_user = mock.Mock()
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "role": "client"
    }

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.get.return_value = fake_user

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "user@test.com"


def test_change_password_missing_fields(client, app):
    with app.app_context():
        token = create_access_token(identity="1")

    fake_user = mock.Mock()

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.get.return_value = fake_user

        response = client.put(
            "/api/auth/change-password",
            json={},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 400


def test_change_password_wrong_current_password(client, app):
    with app.app_context():
        token = create_access_token(identity="1")

    fake_user = mock.Mock()
    fake_user.check_password.return_value = False

    with mock.patch("routes.auth_routes.User.query") as mock_query:
        mock_query.get.return_value = fake_user

        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": "wrong",
                "new_password": "Password456"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401


def test_change_password_success(client, app):
    with app.app_context():
        token = create_access_token(identity="1")

    fake_user = mock.Mock()
    fake_user.check_password.return_value = True

    with mock.patch("routes.auth_routes.User.query") as mock_query, \
         mock.patch("routes.auth_routes.db.session") as mock_session:

        mock_query.get.return_value = fake_user

        response = client.put(
            "/api/auth/change-password",
            json={
                "current_password": "Password123",
                "new_password": "Password456"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    fake_user.set_password.assert_called_once_with("Password456")
    mock_session.commit.assert_called_once()