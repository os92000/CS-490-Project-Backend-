from io import BytesIO
from unittest import mock

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def coach_headers(app):
    with app.app_context():
        token = create_access_token(identity="2")
        return {"Authorization": f"Bearer {token}"}


def test_get_my_progress_photos_success(client, auth_headers):
    fake_photo = mock.Mock()
    fake_photo.to_dict.return_value = {
        "id": 10,
        "user_id": 1,
        "photo_url": "/uploads/progress_photos/p1.jpg",
        "category": "front",
    }

    with mock.patch("routes.progress_photos_routes.ProgressPhoto.query") as photo_query:
        photo_query.filter_by.return_value.order_by.return_value.all.return_value = [
            fake_photo
        ]

        response = client.get("/api/progress-photos", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["photos"][0]["category"] == "front"


def test_upload_progress_photo_requires_file(client, auth_headers):
    response = client.post(
        "/api/progress-photos",
        data={},
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_upload_progress_photo_invalid_category(client, auth_headers):
    response = client.post(
        "/api/progress-photos",
        data={
            "photo": (BytesIO(b"fake image data"), "progress.jpg"),
            "category": "diagonal",
        },
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_upload_progress_photo_success(client, auth_headers):
    fake_photo = mock.Mock()
    fake_photo.to_dict.return_value = {
        "id": 1,
        "user_id": 1,
        "photo_url": "/uploads/progress_photos/abc.jpg",
        "category": "front",
        "notes": "week 1",
        "date": "2026-05-01",
    }

    with mock.patch("routes.progress_photos_routes.save_uploaded_file", return_value="abc.jpg"), \
         mock.patch("routes.progress_photos_routes.ProgressPhoto", return_value=fake_photo), \
         mock.patch("routes.progress_photos_routes.db.session") as session:

        response = client.post(
            "/api/progress-photos",
            data={
                "photo": (BytesIO(b"fake image data"), "progress.jpg"),
                "category": "front",
                "notes": "week 1",
                "date": "2026-05-01",
            },
            headers=auth_headers,
            content_type="multipart/form-data",
        )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["photo_url"] == "/uploads/progress_photos/abc.jpg"
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_delete_progress_photo_not_found(client, auth_headers):
    with mock.patch("routes.progress_photos_routes.ProgressPhoto.query") as photo_query:
        photo_query.filter_by.return_value.first.return_value = None

        response = client.delete("/api/progress-photos/42", headers=auth_headers)

    assert response.status_code == 404


def test_get_client_progress_photos_forbidden_for_non_coach(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.progress_photos_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.get("/api/progress-photos/client/5", headers=auth_headers)

    assert response.status_code == 403


def test_get_client_progress_photos_requires_active_relationship(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.progress_photos_routes.User.query") as user_query, \
         mock.patch("routes.progress_photos_routes.CoachRelationship.query") as rel_query:

        user_query.get.return_value = fake_user
        rel_query.filter_by.return_value.first.return_value = None

        response = client.get("/api/progress-photos/client/9", headers=coach_headers)

    assert response.status_code == 403


def test_get_client_progress_photos_success(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"
    fake_rel = mock.Mock()

    fake_photo = mock.Mock()
    fake_photo.to_dict.return_value = {
        "id": 77,
        "user_id": 9,
        "photo_url": "/uploads/progress_photos/client9.jpg",
        "category": "side",
    }

    with mock.patch("routes.progress_photos_routes.User.query") as user_query, \
         mock.patch("routes.progress_photos_routes.CoachRelationship.query") as rel_query, \
         mock.patch("routes.progress_photos_routes.ProgressPhoto.query") as photo_query:

        user_query.get.return_value = fake_user
        rel_query.filter_by.return_value.first.return_value = fake_rel
        photo_query.filter_by.return_value.order_by.return_value.all.return_value = [
            fake_photo
        ]

        response = client.get("/api/progress-photos/client/9", headers=coach_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["photos"][0]["category"] == "side"
