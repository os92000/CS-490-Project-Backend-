from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, WorkoutLog, MealLog, BodyMetric, CoachRelationship
from utils.helpers import success_response, error_response
from sqlalchemy import func
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/workout-summary', methods=['GET'])
@jwt_required()
def workout_summary():
    """Get workout analytics summary"""
    user_id = int(get_jwt_identity())

    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.now().date() - timedelta(days=days)

        total_workouts = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date
        ).count()

        total_duration = db.session.query(func.sum(WorkoutLog.duration_minutes)).filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date
        ).scalar() or 0

        avg_rating = db.session.query(func.avg(WorkoutLog.rating)).filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date,
            WorkoutLog.rating.isnot(None)
        ).scalar() or 0

        return success_response({
            'total_workouts': total_workouts,
            'total_duration_minutes': int(total_duration),
            'average_rating': round(float(avg_rating), 1) if avg_rating else 0,
            'period_days': days
        }, 'Workout summary retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve analytics', 500, str(e))

@analytics_bp.route('/nutrition-summary', methods=['GET'])
@jwt_required()
def nutrition_summary():
    """Get nutrition analytics summary"""
    user_id = int(get_jwt_identity())

    try:
        days = int(request.args.get('days', 7))
        start_date = datetime.now().date() - timedelta(days=days)

        avg_calories = db.session.query(func.avg(MealLog.calories)).filter(
            MealLog.user_id == user_id,
            MealLog.date >= start_date,
            MealLog.calories.isnot(None)
        ).scalar() or 0

        return success_response({
            'average_daily_calories': round(float(avg_calories), 0) if avg_calories else 0,
            'period_days': days
        }, 'Nutrition summary retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve nutrition analytics', 500, str(e))

@analytics_bp.route('/progress', methods=['GET'])
@jwt_required()
def progress_tracking():
    """Get body metrics progress"""
    user_id = int(get_jwt_identity())

    try:
        metrics = BodyMetric.query.filter_by(user_id=user_id).order_by(BodyMetric.date.desc()).limit(30).all()

        return success_response({
            'metrics': [m.to_dict() for m in metrics]
        }, 'Progress data retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve progress', 500, str(e))
