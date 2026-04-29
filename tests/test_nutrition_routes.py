from datetime import date
from unittest import mock

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def auth_headers(app):
    with app.app_context():
        token = create_access_token(identity="1")
        return {"Authorization": f"Bearer {token}"}


def test_meals_requires_login(client):
    response = client.get("/api/nutrition/meals")

    assert response.status_code == 401


def test_get_meals_success(client, auth_headers):
    fake_meal = mock.Mock()
    fake_meal.to_dict.return_value = {
        "id": 1,
        "meal_type": "lunch",
        "food_items": "Chicken and rice"
    }

    with mock.patch("routes.nutrition_routes.MealLog.query") as meal_query:
        meal_query.filter_by.return_value.order_by.return_value.all.return_value = [fake_meal]

        response = client.get("/api/nutrition/meals", headers=auth_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["meals"][0]["meal_type"] == "lunch"


def test_create_meal_missing_date(client, auth_headers):
    response = client.post(
        "/api/nutrition/meals",
        json={"meal_type": "lunch"},
        headers=auth_headers
    )

    assert response.status_code == 400


def test_create_meal_success(client, auth_headers):
    fake_meal = mock.Mock()
    fake_meal.to_dict.return_value = {
        "id": 1,
        "meal_type": "lunch",
        "food_items": "Chicken, rice, broccoli",
        "calories": 500
    }

    with mock.patch("routes.nutrition_routes.MealLog") as meal_class, \
         mock.patch("routes.nutrition_routes.db.session") as session:

        meal_class.return_value = fake_meal

        response = client.post(
            "/api/nutrition/meals",
            json={
                "date": "2024-01-01",
                "meal_type": "lunch",
                "food_items": "Chicken, rice, broccoli",
                "calories": 500,
                "protein_g": 40,
                "carbs_g": 50,
                "fat_g": 10
            },
            headers=auth_headers
        )

    assert response.status_code == 201
    assert response.get_json()["success"] is True
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_delete_meal_not_found(client, auth_headers):
    with mock.patch("routes.nutrition_routes.MealLog.query") as meal_query:
        meal_query.filter_by.return_value.first.return_value = None

        response = client.delete("/api/nutrition/meals/1", headers=auth_headers)

    assert response.status_code == 404


def test_delete_meal_not_current_day(client, auth_headers):
    fake_meal = mock.Mock()
    fake_meal.date = date(2020, 1, 1)

    with mock.patch("routes.nutrition_routes.MealLog.query") as meal_query, \
         mock.patch("routes.nutrition_routes.is_current_day", return_value=False):

        meal_query.filter_by.return_value.first.return_value = fake_meal

        response = client.delete("/api/nutrition/meals/1", headers=auth_headers)

    assert response.status_code == 403


def test_delete_meal_success(client, auth_headers):
    fake_meal = mock.Mock()
    fake_meal.date = date.today()

    with mock.patch("routes.nutrition_routes.MealLog.query") as meal_query, \
         mock.patch("routes.nutrition_routes.is_current_day", return_value=True), \
         mock.patch("routes.nutrition_routes.db.session") as session:

        meal_query.filter_by.return_value.first.return_value = fake_meal

        response = client.delete("/api/nutrition/meals/1", headers=auth_headers)

    assert response.status_code == 200
    session.delete.assert_called_once_with(fake_meal)
    session.commit.assert_called_once()


def test_get_body_metrics_success(client, auth_headers):
    fake_metric = mock.Mock()
    fake_metric.to_dict.return_value = {
        "id": 1,
        "weight_kg": 72
    }

    with mock.patch("routes.nutrition_routes.BodyMetric.query") as metric_query:
        metric_query.filter_by.return_value.order_by.return_value.all.return_value = [fake_metric]

        response = client.get("/api/nutrition/metrics", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["data"]["metrics"][0]["weight_kg"] == 72


def test_create_body_metric_missing_date(client, auth_headers):
    response = client.post(
        "/api/nutrition/metrics",
        json={"weight_kg": 72},
        headers=auth_headers
    )

    assert response.status_code == 400


def test_create_body_metric_success(client, auth_headers):
    fake_metric = mock.Mock()
    fake_metric.to_dict.return_value = {
        "id": 1,
        "weight_kg": 72
    }

    with mock.patch("routes.nutrition_routes.BodyMetric") as metric_class, \
         mock.patch("routes.nutrition_routes.db.session") as session:

        metric_class.return_value = fake_metric

        response = client.post(
            "/api/nutrition/metrics",
            json={
                "date": "2024-01-01",
                "weight_kg": 72,
                "body_fat_percentage": 20
            },
            headers=auth_headers
        )

    assert response.status_code == 201
    assert response.get_json()["success"] is True
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_delete_body_metric_not_found(client, auth_headers):
    with mock.patch("routes.nutrition_routes.BodyMetric.query") as metric_query:
        metric_query.filter_by.return_value.first.return_value = None

        response = client.delete("/api/nutrition/metrics/1", headers=auth_headers)

    assert response.status_code == 404


def test_delete_body_metric_success(client, auth_headers):
    fake_metric = mock.Mock()
    fake_metric.date = date.today()

    with mock.patch("routes.nutrition_routes.BodyMetric.query") as metric_query, \
         mock.patch("routes.nutrition_routes.is_current_day", return_value=True), \
         mock.patch("routes.nutrition_routes.db.session") as session:

        metric_query.filter_by.return_value.first.return_value = fake_metric

        response = client.delete("/api/nutrition/metrics/1", headers=auth_headers)

    assert response.status_code == 200
    session.delete.assert_called_once_with(fake_metric)
    session.commit.assert_called_once()


def test_get_wellness_logs_success(client, auth_headers):
    fake_log = mock.Mock()
    fake_log.to_dict.return_value = {
        "id": 1,
        "mood": "happy"
    }

    with mock.patch("routes.nutrition_routes.WellnessLog.query") as wellness_query:
        wellness_query.filter_by.return_value.order_by.return_value.all.return_value = [fake_log]

        response = client.get("/api/nutrition/wellness", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["data"]["wellness"][0]["mood"] == "happy"


def test_create_wellness_missing_date(client, auth_headers):
    response = client.post(
        "/api/nutrition/wellness",
        json={"mood": "happy"},
        headers=auth_headers
    )

    assert response.status_code == 400


def test_create_wellness_success(client, auth_headers):
    fake_log = mock.Mock()
    fake_log.to_dict.return_value = {
        "id": 1,
        "mood": "happy",
        "energy_level": 8
    }

    with mock.patch("routes.nutrition_routes.WellnessLog") as wellness_class, \
         mock.patch("routes.nutrition_routes.db.session") as session:

        wellness_class.return_value = fake_log

        response = client.post(
            "/api/nutrition/wellness",
            json={
                "date": "2024-01-01",
                "mood": "happy",
                "energy_level": 8,
                "stress_level": 3,
                "sleep_hours": 7
            },
            headers=auth_headers
        )

    assert response.status_code == 201
    assert response.get_json()["success"] is True
    session.add.assert_called_once()
    session.commit.assert_called_once()


def test_delete_wellness_not_found(client, auth_headers):
    with mock.patch("routes.nutrition_routes.WellnessLog.query") as wellness_query:
        wellness_query.filter_by.return_value.first.return_value = None

        response = client.delete("/api/nutrition/wellness/1", headers=auth_headers)

    assert response.status_code == 404


def test_delete_wellness_success(client, auth_headers):
    fake_log = mock.Mock()
    fake_log.date = date.today()

    with mock.patch("routes.nutrition_routes.WellnessLog.query") as wellness_query, \
         mock.patch("routes.nutrition_routes.is_current_day", return_value=True), \
         mock.patch("routes.nutrition_routes.db.session") as session:

        wellness_query.filter_by.return_value.first.return_value = fake_log

        response = client.delete("/api/nutrition/wellness/1", headers=auth_headers)

    assert response.status_code == 200
    session.delete.assert_called_once_with(fake_log)
    session.commit.assert_called_once()


def test_daily_metrics_missing_date(client, auth_headers):
    response = client.post(
        "/api/nutrition/daily-metrics",
        json={},
        headers=auth_headers
    )

    assert response.status_code in [400, 500]


def test_meal_plans_missing_title(client, auth_headers):
    response = client.post(
        "/api/nutrition/meal-plans",
        json={},
        headers=auth_headers
    )

    assert response.status_code in [400, 500]