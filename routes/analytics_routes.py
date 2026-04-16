from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import MealLog, BodyMetric, WorkoutLog
from utils.helpers import success_response, error_response
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

VALID_PERIODS = {'day', 'week', 'month', 'year'}


def _parse_iso_date(value, field_name):
    try:
        return datetime.fromisoformat(value).date()
    except (ValueError, TypeError):
        raise ValueError(f'Invalid {field_name}. Expected YYYY-MM-DD')


def _period_defaults(period):
    # Defaults balance chart usefulness and payload size.
    return {
        'day': 30,
        'week': 84,
        'month': 365,
        'year': 1825,
    }.get(period, 30)


def _resolve_date_range():
    period = request.args.get('period', 'month').lower()
    if period not in VALID_PERIODS:
        raise ValueError('Invalid period. Use day, week, month, or year')

    start_date_arg = request.args.get('start_date') or request.args.get('from')
    end_date_arg = request.args.get('end_date') or request.args.get('to')
    days_arg = request.args.get('days')

    today = datetime.utcnow().date()

    if start_date_arg and end_date_arg:
        start_date = _parse_iso_date(start_date_arg, 'start_date')
        end_date = _parse_iso_date(end_date_arg, 'end_date')
    elif days_arg is not None:
        days = int(days_arg)
        if days < 1:
            raise ValueError('days must be >= 1')
        end_date = today
        start_date = end_date - timedelta(days=days - 1)
    else:
        end_date = today
        start_date = end_date - timedelta(days=_period_defaults(period) - 1)

    if start_date > end_date:
        raise ValueError('start_date must be before or equal to end_date')

    return period, start_date, end_date


def _period_start(date_value, period):
    if period == 'day':
        return date_value
    if period == 'week':
        return date_value - timedelta(days=date_value.weekday())
    if period == 'month':
        return date_value.replace(day=1)
    if period == 'year':
        return date_value.replace(month=1, day=1)
    return date_value


def _next_period_start(start_value, period):
    if period == 'day':
        return start_value + timedelta(days=1)
    if period == 'week':
        return start_value + timedelta(days=7)
    if period == 'month':
        if start_value.month == 12:
            return start_value.replace(year=start_value.year + 1, month=1, day=1)
        return start_value.replace(month=start_value.month + 1, day=1)
    if period == 'year':
        return start_value.replace(year=start_value.year + 1, month=1, day=1)
    return start_value + timedelta(days=1)


def _bucket_label(start_value, period):
    if period == 'day':
        return start_value.strftime('%Y-%m-%d')
    if period == 'week':
        iso_year, iso_week, _ = start_value.isocalendar()
        return f'{iso_year}-W{iso_week:02d}'
    if period == 'month':
        return start_value.strftime('%Y-%m')
    if period == 'year':
        return str(start_value.year)
    return start_value.strftime('%Y-%m-%d')


def _bucket_labels_in_range(start_date, end_date, period):
    labels = []
    cursor = _period_start(start_date, period)
    end_cursor = _period_start(end_date, period)

    while cursor <= end_cursor:
        labels.append(_bucket_label(cursor, period))
        cursor = _next_period_start(cursor, period)

    return labels


def _build_workout_chart_series(user_id, period, start_date, end_date):
    bucket_labels = _bucket_labels_in_range(start_date, end_date, period)

    workouts_map = {
        label: {
            'bucket': label,
            'workouts_completed': 0,
            'total_duration_minutes': 0,
            'average_rating': None,
            '_rating_sum': 0,
            '_rating_count': 0,
        }
        for label in bucket_labels
    }

    workout_logs = WorkoutLog.query.filter(
        WorkoutLog.client_id == user_id,
        WorkoutLog.date >= start_date,
        WorkoutLog.date <= end_date
    ).all()

    for log in workout_logs:
        label = _bucket_label(_period_start(log.date, period), period)
        row = workouts_map.get(label)
        if not row:
            continue
        if log.completed is not False:
            row['workouts_completed'] += 1
        if log.duration_minutes is not None:
            row['total_duration_minutes'] += int(log.duration_minutes)
        if log.rating is not None:
            row['_rating_sum'] += int(log.rating)
            row['_rating_count'] += 1

    workouts_series = []
    for label in bucket_labels:
        row = workouts_map[label]
        rating = None
        if row['_rating_count'] > 0:
            rating = round(row['_rating_sum'] / row['_rating_count'], 2)
        workouts_series.append({
            'bucket': label,
            'workouts_completed': row['workouts_completed'],
            'total_duration_minutes': row['total_duration_minutes'],
            'average_rating': rating,
        })

    return {
        'workouts': workouts_series
    }

@analytics_bp.route('/workout-summary', methods=['GET'])
@jwt_required()
def workout_summary():
    """Get workout analytics summary"""
    user_id = int(get_jwt_identity())

    try:
        period, start_date, end_date = _resolve_date_range()

        logs = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date,
            WorkoutLog.date <= end_date
        ).all()

        total_workouts = sum(1 for log in logs if log.completed is not False)
        total_duration = sum(int(log.duration_minutes or 0) for log in logs)
        ratings = [int(log.rating) for log in logs if log.rating is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        period_days = max((end_date - start_date).days + 1, 1)
        workout_frequency_per_week = round((total_workouts / period_days) * 7, 1)

        return success_response({
            'total_workouts': total_workouts,
            'total_duration_minutes': int(total_duration),
            'average_rating': avg_rating,
            'workout_frequency_per_week': workout_frequency_per_week,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }, 'Workout summary retrieved', 200)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response('Failed to retrieve analytics', 500, str(e))

@analytics_bp.route('/nutrition-summary', methods=['GET'])
@jwt_required()
def nutrition_summary():
    """Get nutrition analytics summary"""
    user_id = int(get_jwt_identity())

    try:
        period, start_date, end_date = _resolve_date_range()

        meal_logs = MealLog.query.filter(
            MealLog.user_id == user_id,
            MealLog.date >= start_date,
            MealLog.date <= end_date
        ).all()

        period_days = max((end_date - start_date).days + 1, 1)
        total_calories = sum(int(log.calories or 0) for log in meal_logs)
        total_protein = sum(float(log.protein_g or 0) for log in meal_logs)
        total_carbs = sum(float(log.carbs_g or 0) for log in meal_logs)

        avg_calories = round(total_calories / period_days, 2)
        avg_protein = round(total_protein / period_days, 2)
        avg_carbs = round(total_carbs / period_days, 2)

        return success_response({
            'average_daily_calories': avg_calories,
            'average_protein_g': avg_protein,
            'average_carbs_g': avg_carbs,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }, 'Nutrition summary retrieved', 200)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response('Failed to retrieve nutrition analytics', 500, str(e))

@analytics_bp.route('/progress', methods=['GET'])
@jwt_required()
def progress_tracking():
    """Get body metrics progress"""
    user_id = int(get_jwt_identity())

    try:
        period, start_date, end_date = _resolve_date_range()
        metrics = BodyMetric.query.filter(
            BodyMetric.user_id == user_id,
            BodyMetric.date >= start_date,
            BodyMetric.date <= end_date
        ).order_by(BodyMetric.date.desc()).all()

        return success_response({
            'metrics': [m.to_dict() for m in metrics],
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        }, 'Progress data retrieved', 200)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response('Failed to retrieve progress', 500, str(e))


@analytics_bp.route('/charts', methods=['GET'])
@jwt_required()
def chart_series():
    """Get workout chart series for MyWorkouts analytics tab"""
    user_id = int(get_jwt_identity())

    try:
        period, start_date, end_date = _resolve_date_range()
        series = _build_workout_chart_series(user_id, period, start_date, end_date)

        return success_response({
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'series': series,
        }, 'Analytics chart data retrieved', 200)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response('Failed to retrieve chart data', 500, str(e))
