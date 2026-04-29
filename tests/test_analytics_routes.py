from datetime import date
from types import SimpleNamespace
from unittest import mock

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
        return {"Authorization": f"Bearer {token}"}


def test_workout_summary_requires_login(client):
    response = client.get("/api/analytics/workout-summary")

    assert response.status_code == 401


def test_workout_summary_invalid_period(client, auth_headers):
    response = client.get(
        "/api/analytics/workout-summary?period=bad",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_workout_summary_success(client, auth_headers):
    fake_logs = [
        SimpleNamespace(
            completed=True,
            duration_minutes=30,
            rating=5
        ),
        SimpleNamespace(
            completed=True,
            duration_minutes=45,
            rating=4
        ),
        SimpleNamespace(
            completed=False,
            duration_minutes=20,
            rating=None
        ),
    ]

    with mock.patch("routes.analytics_routes.WorkoutLog.query") as mock_query:
        mock_query.filter.return_value.all.return_value = fake_logs

        response = client.get(
            "/api/analytics/workout-summary?start_date=2024-01-01&end_date=2024-01-07",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["total_workouts"] == 2
    assert data["data"]["total_duration_minutes"] == 95
    assert data["data"]["average_rating"] == 4.5


def test_nutrition_summary_success(client, auth_headers):
    fake_meals = [
        SimpleNamespace(
            calories=500,
            protein_g=40,
            carbs_g=50
        ),
        SimpleNamespace(
            calories=700,
            protein_g=60,
            carbs_g=80
        ),
    ]

    with mock.patch("routes.analytics_routes.MealLog.query") as mock_query:
        mock_query.filter.return_value.all.return_value = fake_meals

        response = client.get(
            "/api/analytics/nutrition-summary?start_date=2024-01-01&end_date=2024-01-02",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["meal_logs_count"] == 2
    assert data["data"]["average_daily_calories"] == 600
    assert data["data"]["average_protein_g"] == 50
    assert data["data"]["average_carbs_g"] == 65


def test_progress_tracking_success(client, auth_headers):
    fake_metric = mock.Mock()
    fake_metric.to_dict.return_value = {
        "weight": 170,
        "body_fat_percentage": 20,
        "date": "2024-01-01"
    }

    with mock.patch("routes.analytics_routes.BodyMetric.query") as mock_query:
        mock_query.filter.return_value.order_by.return_value.all.return_value = [fake_metric]

        response = client.get(
            "/api/analytics/progress?start_date=2024-01-01&end_date=2024-01-01",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert len(data["data"]["metrics"]) == 1
    assert data["data"]["metrics"][0]["weight"] == 170


def test_charts_success(client, auth_headers):
    fake_logs = [
        SimpleNamespace(
            date=date(2024, 1, 1),
            completed=True,
            duration_minutes=30,
            rating=5
        ),
        SimpleNamespace(
            date=date(2024, 1, 2),
            completed=True,
            duration_minutes=45,
            rating=3
        ),
    ]

    with mock.patch("routes.analytics_routes.WorkoutLog.query") as mock_query:
        mock_query.filter.return_value.all.return_value = fake_logs

        response = client.get(
            "/api/analytics/charts?period=day&start_date=2024-01-01&end_date=2024-01-02",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["period"] == "day"
    assert "series" in data["data"]
    assert "workouts" in data["data"]["series"]