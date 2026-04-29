from unittest import mock

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_headers(app):
    with app.app_context():
        token = create_access_token(identity="2")
        return {"Authorization": f"Bearer {token}"}


def test_update_user_role_requires_login(client):
    response = client.patch("/api/users/1/role", json={"role": "client"})

    assert response.status_code == 401


def test_update_user_role_unauthorized(client, other_headers):
    response = client.patch(
        "/api/users/1/role",
        json={"role": "client"},
        headers=other_headers
    )

    assert response.status_code == 403


def test_update_user_role_user_not_found(client, auth_headers):
    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = None

        response = client.patch(
            "/api/users/1/role",
            json={"role": "client"},
            headers=auth_headers
        )

    assert response.status_code == 404


def test_update_user_role_missing_role(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "none"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.patch(
            "/api/users/1/role",
            json={},
            headers=auth_headers
        )

    assert response.status_code == 400


def test_update_user_role_invalid_role(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "none"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.patch(
            "/api/users/1/role",
            json={"role": "bad-role"},
            headers=auth_headers
        )

    assert response.status_code == 400


def test_update_user_role_admin_not_allowed(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.patch(
            "/api/users/1/role",
            json={"role": "admin"},
            headers=auth_headers
        )

    assert response.status_code == 403


def test_update_user_role_client_to_coach_blocked(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.patch(
            "/api/users/1/role",
            json={"role": "coach"},
            headers=auth_headers
        )

    assert response.status_code == 403


def test_update_user_role_success(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "none"
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "role": "client"
    }

    with mock.patch("routes.users_routes.User.query") as user_query, \
         mock.patch("routes.users_routes.db.session") as session:

        user_query.get.return_value = fake_user

        response = client.patch(
            "/api/users/1/role",
            json={"role": "client"},
            headers=auth_headers
        )

    assert response.status_code == 200
    assert fake_user.role == "client"
    assert response.get_json()["success"] is True
    session.commit.assert_called_once()


def test_get_user_profile_requires_login(client):
    response = client.get("/api/users/1/profile")

    assert response.status_code == 401


def test_get_user_profile_not_found(client, auth_headers):
    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = None

        response = client.get("/api/users/1/profile", headers=auth_headers)

    assert response.status_code == 404


def test_get_user_profile_success(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "profile": {"first_name": "John"}
    }

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.get("/api/users/1/profile", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "user@test.com"


def test_update_user_profile_unauthorized(client, other_headers):
    response = client.put(
        "/api/users/1/profile",
        json={"first_name": "John"},
        headers=other_headers
    )

    assert response.status_code == 403


def test_update_user_profile_user_not_found(client, auth_headers):
    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = None

        response = client.put(
            "/api/users/1/profile",
            json={"first_name": "John"},
            headers=auth_headers
        )

    assert response.status_code == 404


def test_update_user_profile_success_existing_profile(client, auth_headers):
    fake_profile = mock.Mock()

    fake_user = mock.Mock()
    fake_user.profile = fake_profile
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "profile": {
            "first_name": "John",
            "last_name": "Doe"
        }
    }

    with mock.patch("routes.users_routes.User.query") as user_query, \
         mock.patch("routes.users_routes.db.session") as session:

        user_query.get.return_value = fake_user

        response = client.put(
            "/api/users/1/profile",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Hello",
                "phone": "123"
            },
            headers=auth_headers
        )

    assert response.status_code == 200
    assert fake_profile.first_name == "John"
    assert fake_profile.last_name == "Doe"
    assert fake_profile.bio == "Hello"
    assert fake_profile.phone == "123"
    session.commit.assert_called_once()


def test_update_user_profile_creates_profile_if_missing(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.profile = None
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "profile": {
            "first_name": "New"
        }
    }

    fake_profile = mock.Mock()

    with mock.patch("routes.users_routes.User.query") as user_query, \
         mock.patch("routes.users_routes.UserProfile", return_value=fake_profile), \
         mock.patch("routes.users_routes.db.session") as session:

        user_query.get.return_value = fake_user

        response = client.put(
            "/api/users/1/profile",
            json={"first_name": "New"},
            headers=auth_headers
        )

    assert response.status_code == 200
    session.add.assert_called_once_with(fake_profile)
    session.commit.assert_called_once()


def test_delete_user_account_unauthorized(client, other_headers):
    current_user = mock.Mock()
    current_user.role = "client"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = current_user

        response = client.delete("/api/users/1", headers=other_headers)

    assert response.status_code == 403


def test_submit_role_change_request_user_not_found(client, auth_headers):
    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = None

        response = client.post(
            "/api/users/role-requests",
            json={"requested_role": "coach"},
            headers=auth_headers
        )

    assert response.status_code == 404


def test_submit_role_change_request_non_client(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.post(
            "/api/users/role-requests",
            json={"requested_role": "coach"},
            headers=auth_headers
        )

    assert response.status_code == 403


def test_submit_role_change_request_invalid_role(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.users_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.post(
            "/api/users/role-requests",
            json={"requested_role": "admin"},
            headers=auth_headers
        )

    assert response.status_code == 400


def test_submit_role_change_request_duplicate_pending(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    existing_request = mock.Mock()

    with mock.patch("routes.users_routes.User.query") as user_query, \
         mock.patch("routes.users_routes.RoleChangeRequest.query") as req_query:

        user_query.get.return_value = fake_user
        req_query.filter_by.return_value.first.return_value = existing_request

        response = client.post(
            "/api/users/role-requests",
            json={"requested_role": "coach"},
            headers=auth_headers
        )

    assert response.status_code == 409


def test_submit_role_change_request_success(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    fake_request = mock.Mock()
    fake_request.to_dict.return_value = {
        "id": 1,
        "requested_role": "coach",
        "status": "pending"
    }

    with mock.patch("routes.users_routes.User.query") as user_query, \
         mock.patch("routes.users_routes.RoleChangeRequest") as request_class, \
         mock.patch("routes.users_routes.db.session") as session:

        user_query.get.return_value = fake_user
        request_class.query.filter_by.return_value.first.return_value = None
        request_class.return_value = fake_request

        response = client.post(
            "/api/users/role-requests",
            json={
                "requested_role": "coach",
                "reason": "I want to coach clients"
            },
            headers=auth_headers
        )

    assert response.status_code == 201
    assert response.get_json()["success"] is True
    session.add.assert_called_once_with(fake_request)
    session.commit.assert_called_once()


def test_get_my_role_change_request_none(client, auth_headers):
    with mock.patch("routes.users_routes.RoleChangeRequest.query") as req_query:
        req_query.filter_by.return_value.order_by.return_value.first.return_value = None

        response = client.get(
            "/api/users/role-requests/me",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert response.get_json()["data"] is None


def test_get_my_role_change_request_success(client, auth_headers):
    fake_request = mock.Mock()
    fake_request.to_dict.return_value = {
        "id": 1,
        "requested_role": "coach",
        "status": "pending"
    }

    with mock.patch("routes.users_routes.RoleChangeRequest.query") as req_query:
        req_query.filter_by.return_value.order_by.return_value.first.return_value = fake_request

        response = client.get(
            "/api/users/role-requests/me",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "pending"