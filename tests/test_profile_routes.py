from io import BytesIO
from unittest import mock

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
        return {"Authorization": f"Bearer {token}"}


def test_get_profile_requires_login(client):
    response = client.get("/api/profile")

    assert response.status_code == 401


def test_get_profile_not_found(client, auth_headers):
    with mock.patch("routes.profile_routes.User.query") as user_query:
        user_query.get.return_value = None

        response = client.get("/api/profile", headers=auth_headers)

    assert response.status_code == 404


def test_get_profile_success(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.to_dict.return_value = {
        "id": 1,
        "email": "user@test.com",
        "profile": {
            "first_name": "John",
            "last_name": "Doe"
        }
    }

    with mock.patch("routes.profile_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.get("/api/profile", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == "user@test.com"


def test_update_profile_existing_profile_success(client, auth_headers):
    fake_profile = mock.Mock()
    fake_profile.to_dict.return_value = {
        "first_name": "Mark",
        "last_name": "Lopez",
        "phone": "+1 973 417 9543"
    }

    with mock.patch("routes.profile_routes.UserProfile.query") as profile_query, \
         mock.patch("routes.profile_routes.db.session") as session:

        profile_query.filter_by.return_value.first.return_value = fake_profile

        response = client.put(
            "/api/profile",
            json={
                "first_name": "Mark",
                "last_name": "Lopez",
                "bio": "Hello",
                "phone": "+1 973 417 9543",
                "profile_picture": "/uploads/profiles/test.png"
            },
            headers=auth_headers
        )

    assert response.status_code == 200
    assert fake_profile.first_name == "Mark"
    assert fake_profile.last_name == "Lopez"
    assert fake_profile.bio == "Hello"
    assert fake_profile.phone == "+1 973 417 9543"
    assert fake_profile.profile_picture == "/uploads/profiles/test.png"
    session.commit.assert_called_once()


def test_update_profile_creates_profile_if_missing(client, auth_headers):
    fake_profile = mock.Mock()
    fake_profile.to_dict.return_value = {
        "first_name": "New",
        "last_name": "User"
    }

    with mock.patch("routes.profile_routes.UserProfile.query") as profile_query, \
         mock.patch("routes.profile_routes.db.session") as session:

        profile_query.filter_by.return_value.first.return_value = fake_profile

        response = client.put(
            "/api/profile",
            json={
                "first_name": "New",
                "last_name": "User"
            },
            headers=auth_headers
        )

    assert response.status_code == 200
    assert response.get_json()["data"]["first_name"] == "New"
    session.commit.assert_called_once()


def test_get_notifications_success(client, auth_headers):
    fake_notification = mock.Mock()
    fake_notification.to_dict.return_value = {
        "id": 1,
        "message": "Hello",
        "read": False
    }

    with mock.patch("routes.profile_routes.Notification.query") as notification_query:
        notification_query.filter_by.return_value.order_by.return_value.all.return_value = [
            fake_notification
        ]

        response = client.get("/api/profile/notifications", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["notifications"][0]["message"] == "Hello"


def test_mark_notification_read_not_found(client, auth_headers):
    with mock.patch("routes.profile_routes.Notification.query") as notification_query:
        notification_query.filter_by.return_value.first.return_value = None

        response = client.patch(
            "/api/profile/notifications/1/read",
            headers=auth_headers
        )

    assert response.status_code == 404


def test_mark_notification_read_success(client, auth_headers):
    fake_notification = mock.Mock()
    fake_notification.to_dict.return_value = {
        "id": 1,
        "read": True
    }

    with mock.patch("routes.profile_routes.Notification.query") as notification_query, \
         mock.patch("routes.profile_routes.db.session") as session:

        notification_query.filter_by.return_value.first.return_value = fake_notification

        response = client.patch(
            "/api/profile/notifications/1/read",
            headers=auth_headers
        )

    assert response.status_code == 200
    assert fake_notification.read is True
    session.commit.assert_called_once()


def test_upload_profile_picture_missing_file(client, auth_headers):
    response = client.post(
        "/api/profile/picture",
        data={},
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_upload_profile_picture_no_filename(client, auth_headers):
    response = client.post(
        "/api/profile/picture",
        data={
            "file": (BytesIO(b"fake image data"), "")
        },
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400


def test_upload_profile_picture_success(client, auth_headers):
    fake_profile = mock.Mock()
    fake_profile.to_dict.return_value = {
        "profile_picture": "/uploads/profiles/avatar.png"
    }

    with mock.patch("routes.profile_routes.UserProfile.query") as profile_query, \
         mock.patch("routes.profile_routes.save_uploaded_file", return_value="avatar.png"), \
         mock.patch("routes.profile_routes.db.session") as session:

        profile_query.filter_by.return_value.first.return_value = fake_profile

        response = client.post(
            "/api/profile/picture",
            data={
                "file": (BytesIO(b"fake image data"), "avatar.png")
            },
            headers=auth_headers,
            content_type="multipart/form-data"
        )

    assert response.status_code == 200
    assert fake_profile.profile_picture.replace("\\", "/") == "/uploads/profiles/avatar.png"
    session.commit.assert_called_once()