from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, MealLog, BodyMetric, WellnessLog
from utils.helpers import success_response, error_response
from datetime import datetime, date

nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/api/nutrition')

# Meal Logs
@nutrition_bp.route('/meals', methods=['GET', 'POST'])
@jwt_required()
def meal_logs():
    user_id = int(get_jwt_identity())

    if request.method == 'GET':
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            query = MealLog.query.filter_by(user_id=user_id)
            if start_date:
                query = query.filter(MealLog.date >= datetime.fromisoformat(start_date).date())
            if end_date:
                query = query.filter(MealLog.date <= datetime.fromisoformat(end_date).date())

            logs = query.order_by(MealLog.date.desc()).all()
            return success_response({'meals': [log.to_dict() for log in logs]}, 'Meals retrieved', 200)
        except Exception as e:
            return error_response('Failed to retrieve meals', 500, str(e))

    else:  # POST
        try:
            data = request.get_json()
            if not data or 'date' not in data:
                return error_response('date is required', 400)

            meal = MealLog(
                user_id=user_id,
                date=datetime.fromisoformat(data['date']).date(),
                meal_type=data.get('meal_type'),
                food_items=data.get('food_items'),
                calories=data.get('calories'),
                protein_g=data.get('protein_g'),
                carbs_g=data.get('carbs_g'),
                fat_g=data.get('fat_g'),
                notes=data.get('notes')
            )
            db.session.add(meal)
            db.session.commit()
            return success_response(meal.to_dict(), 'Meal logged', 201)
        except Exception as e:
            db.session.rollback()
            return error_response('Failed to log meal', 500, str(e))

# Body Metrics
@nutrition_bp.route('/metrics', methods=['GET', 'POST'])
@jwt_required()
def body_metrics():
    user_id = int(get_jwt_identity())

    if request.method == 'GET':
        try:
            metrics = BodyMetric.query.filter_by(user_id=user_id).order_by(BodyMetric.date.desc()).all()
            return success_response({'metrics': [m.to_dict() for m in metrics]}, 'Metrics retrieved', 200)
        except Exception as e:
            return error_response('Failed to retrieve metrics', 500, str(e))

    else:  # POST
        try:
            data = request.get_json()
            if not data or 'date' not in data:
                return error_response('date is required', 400)

            metric = BodyMetric(
                user_id=user_id,
                date=datetime.fromisoformat(data['date']).date(),
                weight_kg=data.get('weight_kg'),
                body_fat_percentage=data.get('body_fat_percentage'),
                muscle_mass_kg=data.get('muscle_mass_kg'),
                chest_cm=data.get('chest_cm'),
                waist_cm=data.get('waist_cm'),
                hips_cm=data.get('hips_cm'),
                arms_cm=data.get('arms_cm'),
                thighs_cm=data.get('thighs_cm'),
                notes=data.get('notes')
            )
            db.session.add(metric)
            db.session.commit()
            return success_response(metric.to_dict(), 'Metric logged', 201)
        except Exception as e:
            db.session.rollback()
            return error_response('Failed to log metric', 500, str(e))

# Wellness Logs
@nutrition_bp.route('/wellness', methods=['GET', 'POST'])
@jwt_required()
def wellness_logs():
    user_id = int(get_jwt_identity())

    if request.method == 'GET':
        try:
            logs = WellnessLog.query.filter_by(user_id=user_id).order_by(WellnessLog.date.desc()).all()
            return success_response({'wellness': [l.to_dict() for l in logs]}, 'Wellness logs retrieved', 200)
        except Exception as e:
            return error_response('Failed to retrieve wellness logs', 500, str(e))

    else:  # POST
        try:
            data = request.get_json()
            if not data or 'date' not in data:
                return error_response('date is required', 400)

            log = WellnessLog(
                user_id=user_id,
                date=datetime.fromisoformat(data['date']).date(),
                mood=data.get('mood'),
                energy_level=data.get('energy_level'),
                stress_level=data.get('stress_level'),
                sleep_hours=data.get('sleep_hours'),
                sleep_quality=data.get('sleep_quality'),
                water_intake_ml=data.get('water_intake_ml'),
                notes=data.get('notes')
            )
            db.session.add(log)
            db.session.commit()
            return success_response(log.to_dict(), 'Wellness logged', 201)
        except Exception as e:
            db.session.rollback()
            return error_response('Failed to log wellness', 500, str(e))
