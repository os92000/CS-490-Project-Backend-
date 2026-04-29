from datetime import datetime
from types import SimpleNamespace
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


def test_get_coaches_requires_login(client):
    response = client.get("/api/coaches")

    assert response.status_code == 401


def test_get_coaches_invalid_price_min(client, auth_headers):
    response = client.get(
        "/api/coaches?price_min=bad",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_get_coaches_invalid_price_range(client, auth_headers):
    response = client.get(
        "/api/coaches?price_min=100&price_max=50",
        headers=auth_headers
    )

    assert response.status_code == 400


def test_get_coach_details_not_found(client, auth_headers):
    with mock.patch("routes.coaches_routes.User.query") as mock_query:
        mock_query.get.return_value = None

        response = client.get("/api/coaches/999", headers=auth_headers)

    assert response.status_code == 404


def test_get_coach_details_user_is_not_coach(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.coaches_routes.User.query") as mock_query:
        mock_query.get.return_value = fake_user

        response = client.get("/api/coaches/5", headers=auth_headers)

    assert response.status_code == 400


def test_get_coach_details_success(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.id = 5
    fake_coach.role = "coach"
    fake_coach.to_dict.return_value = {
        "id": 5,
        "email": "coach@test.com",
        "role": "coach"
    }

    fake_survey = mock.Mock()
    fake_survey.to_dict.return_value = {"bio": "Coach bio"}

    fake_spec = mock.Mock()
    fake_spec.to_dict.return_value = {"id": 1, "name": "Weight Loss"}

    fake_availability = mock.Mock()
    fake_availability.to_dict.return_value = {"day_of_week": 1}

    fake_price = mock.Mock()
    fake_price.to_dict.return_value = {"price": "100.00"}

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.CoachApplication.query") as app_query, \
         mock.patch("routes.coaches_routes.CoachSurvey.query") as survey_query, \
         mock.patch("routes.coaches_routes.CoachSpecialization.query") as spec_query, \
         mock.patch("routes.coaches_routes.CoachAvailability.query") as avail_query, \
         mock.patch("routes.coaches_routes.CoachPricing.query") as pricing_query, \
         mock.patch("routes.coaches_routes.Review.query") as review_query, \
         mock.patch("routes.coaches_routes.db.session") as session:

        user_query.get.return_value = fake_coach
        app_query.filter_by.return_value.first.return_value = None
        survey_query.filter_by.return_value.first.return_value = fake_survey
        spec_query.filter_by.return_value.all.return_value = [fake_spec]
        avail_query.filter_by.return_value.all.return_value = [fake_availability]
        pricing_query.filter_by.return_value.all.return_value = [fake_price]
        session.query.return_value.filter_by.return_value.scalar.return_value = 4.5
        review_query.filter_by.return_value.count.return_value = 2

        response = client.get("/api/coaches/5", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["id"] == 5
    assert data["data"]["rating"]["average"] == 4.5


def test_hire_coach_not_found(client, auth_headers):
    with mock.patch("routes.coaches_routes.User.query") as mock_query:
        mock_query.get.return_value = None

        response = client.post("/api/coaches/5/hire", headers=auth_headers)

    assert response.status_code == 404


def test_hire_user_is_not_coach(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.coaches_routes.User.query") as mock_query:
        mock_query.get.return_value = fake_user

        response = client.post("/api/coaches/5/hire", headers=auth_headers)

    assert response.status_code == 400


def test_hire_already_has_active_coach(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.role = "coach"

    fake_relationship = mock.Mock()

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.CoachRelationship.query") as rel_query:

        user_query.get.return_value = fake_coach
        rel_query.filter_by.return_value.first.return_value = fake_relationship

        response = client.post("/api/coaches/5/hire", headers=auth_headers)

    assert response.status_code == 400


def test_hire_success(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.role = "coach"

    fake_request = mock.Mock()
    fake_request.to_dict.return_value = {
        "id": 1,
        "client_id": 1,
        "coach_id": 5,
        "status": "pending"
    }

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.CoachRelationship.query") as rel_query, \
         mock.patch("routes.coaches_routes.ClientRequest") as request_class, \
         mock.patch("routes.coaches_routes.db.session") as session:

        user_query.get.return_value = fake_coach
        rel_query.filter_by.return_value.first.return_value = None

        request_class.query.filter_by.return_value.first.return_value = None
        request_class.return_value = fake_request

        response = client.post("/api/coaches/5/hire", headers=auth_headers)

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["request"]["status"] == "pending"
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_get_specializations_success(client, auth_headers):
    fake_spec = mock.Mock()
    fake_spec.to_dict.return_value = {
        "id": 1,
        "name": "HIIT Training"
    }

    with mock.patch("routes.coaches_routes.Specialization.query") as spec_query:
        spec_query.all.return_value = [fake_spec]

        response = client.get("/api/coaches/specializations", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["specializations"][0]["name"] == "HIIT Training"


def test_respond_to_request_missing_status(client, coach_headers):
    response = client.patch(
        "/api/coaches/requests/1",
        json={},
        headers=coach_headers
    )

    assert response.status_code == 400


def test_respond_to_request_invalid_status(client, coach_headers):
    response = client.patch(
        "/api/coaches/requests/1",
        json={"status": "bad"},
        headers=coach_headers
    )

    assert response.status_code == 400


def test_respond_to_request_not_found(client, coach_headers):
    with mock.patch("routes.coaches_routes.ClientRequest.query") as req_query:
        req_query.get.return_value = None

        response = client.patch(
            "/api/coaches/requests/1",
            json={"status": "accepted"},
            headers=coach_headers
        )

    assert response.status_code == 404


def test_respond_to_request_unauthorized(client, coach_headers):
    fake_request = mock.Mock()
    fake_request.coach_id = 999

    with mock.patch("routes.coaches_routes.ClientRequest.query") as req_query:
        req_query.get.return_value = fake_request

        response = client.patch(
            "/api/coaches/requests/1",
            json={"status": "accepted"},
            headers=coach_headers
        )

    assert response.status_code == 403


def test_respond_to_request_success_denied(client, coach_headers):
    fake_request = mock.Mock()
    fake_request.coach_id = 2
    fake_request.status = "pending"
    fake_request.to_dict.return_value = {
        "id": 1,
        "status": "denied"
    }

    with mock.patch("routes.coaches_routes.ClientRequest.query") as req_query, \
         mock.patch("routes.coaches_routes.db.session") as session:

        req_query.get.return_value = fake_request

        response = client.patch(
            "/api/coaches/requests/1",
            json={"status": "denied"},
            headers=coach_headers
        )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    session.commit.assert_called_once()


def test_submit_review_missing_rating(client, auth_headers):
    response = client.post(
        "/api/coaches/5/review",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 400


def test_submit_review_invalid_rating(client, auth_headers):
    response = client.post(
        "/api/coaches/5/review",
        json={"rating": 6},
        headers=auth_headers
    )

    assert response.status_code == 400


def test_submit_review_no_relationship(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.CoachRelationship.query") as rel_query:

        user_query.get.return_value = fake_coach
        rel_query.filter_by.return_value.first.return_value = None

        response = client.post(
            "/api/coaches/5/review",
            json={"rating": 5, "comment": "Great coach"},
            headers=auth_headers
        )

    assert response.status_code == 403


def test_my_coach_not_found(client, auth_headers):
    with mock.patch("routes.coaches_routes.CoachRelationship.query") as rel_query:
        rel_query.filter_by.return_value.first.return_value = None

        response = client.get("/api/coaches/my-coach", headers=auth_headers)

    assert response.status_code == 404


def test_remove_my_coach_success(client, auth_headers):
    fake_relationship = mock.Mock()
    fake_relationship.status = "active"

    with mock.patch("routes.coaches_routes.CoachRelationship.query") as rel_query, \
         mock.patch("routes.coaches_routes.db.session") as session:

        rel_query.filter_by.return_value.first.return_value = fake_relationship

        response = client.delete("/api/coaches/my-coach", headers=auth_headers)

    assert response.status_code == 200
    assert fake_relationship.status == "ended"
    session.commit.assert_called_once()


def test_report_coach_requires_reason(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_coach

        response = client.post(
            "/api/coaches/5/report",
            json={},
            headers=auth_headers
        )

    assert response.status_code == 400


def test_report_coach_success(client, auth_headers):
    fake_coach = mock.Mock()
    fake_coach.role = "coach"

    fake_report = mock.Mock()
    fake_report.to_dict.return_value = {
        "id": 1,
        "reason": "Inappropriate behavior"
    }

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.ModerationReport") as report_class, \
         mock.patch("routes.coaches_routes.db.session") as session:

        user_query.get.return_value = fake_coach
        report_class.return_value = fake_report

        response = client.post(
            "/api/coaches/5/report",
            json={"reason": "Inappropriate behavior"},
            headers=auth_headers
        )

    assert response.status_code == 201
    assert response.get_json()["success"] is True
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_get_my_availability_non_coach(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.get("/api/coaches/me/availability", headers=auth_headers)

    assert response.status_code == 403


def test_replace_my_availability_missing_slots(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.put(
            "/api/coaches/me/availability",
            json={},
            headers=coach_headers
        )

    assert response.status_code == 400


def test_replace_my_availability_invalid_slot(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.put(
            "/api/coaches/me/availability",
            json={
                "slots": [
                    {
                        "day_of_week": 1,
                        "start_time": "18:00",
                        "end_time": "17:00"
                    }
                ]
            },
            headers=coach_headers
        )

    assert response.status_code == 400


def test_replace_my_pricing_invalid_items(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.put(
            "/api/coaches/me/pricing",
            json={"items": [{"session_type": "Hourly", "price": -5}]},
            headers=coach_headers
        )

    assert response.status_code == 400


def test_get_my_coach_profile_non_coach(client, auth_headers):
    fake_user = mock.Mock()
    fake_user.role = "client"

    with mock.patch("routes.coaches_routes.User.query") as user_query:
        user_query.get.return_value = fake_user

        response = client.get("/api/coaches/me/profile", headers=auth_headers)

    assert response.status_code == 403


def test_update_my_coach_profile_missing_body(client, coach_headers):
    fake_user = mock.Mock()
    fake_user.role = "coach"

    with mock.patch("routes.coaches_routes.User.query") as user_query, \
         mock.patch("routes.coaches_routes.CoachSurvey.query"):

        user_query.get.return_value = fake_user

        response = client.put(
            "/api/coaches/me/profile",
            json=None,
            headers=coach_headers
        )

    assert response.status_code in [400, 500]