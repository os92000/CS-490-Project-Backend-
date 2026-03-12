from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, FitnessSurvey
from utils.validators import is_valid_fitness_level
from utils.helpers import success_response, error_response

surveys_bp = Blueprint('surveys', __name__, url_prefix='/api/surveys')

@surveys_bp.route('/fitness', methods=['POST'])
@jwt_required()
def create_fitness_survey():
    """
    Create or update fitness survey (UC 1.5)
    POST /api/surveys/fitness
    Body: {weight, age, fitness_level, goals}
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return error_response('User not found', 404)

        data = request.get_json()

        # Validate fitness level if provided
        if 'fitness_level' in data and data['fitness_level']:
            if not is_valid_fitness_level(data['fitness_level']):
                return error_response('Invalid fitness level. Must be: beginner, intermediate, or advanced', 400)

        # Check if survey already exists
        survey = FitnessSurvey.query.filter_by(user_id=user_id).first()

        if survey:
            # Update existing survey
            if 'weight' in data:
                survey.weight = data.get('weight')
            if 'age' in data:
                survey.age = data.get('age')
            if 'fitness_level' in data:
                survey.fitness_level = data.get('fitness_level')
            if 'goals' in data:
                survey.goals = data.get('goals')

            message = 'Fitness survey updated successfully'
        else:
            # Create new survey
            survey = FitnessSurvey(
                user_id=user_id,
                weight=data.get('weight'),
                age=data.get('age'),
                fitness_level=data.get('fitness_level'),
                goals=data.get('goals')
            )
            db.session.add(survey)
            message = 'Fitness survey created successfully'

        db.session.commit()

        return success_response(survey.to_dict(), message, 201 if not survey else 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to save fitness survey', 500, str(e))


@surveys_bp.route('/fitness/<int:user_id>', methods=['GET'])
@jwt_required()
def get_fitness_survey(user_id):
    """
    Get fitness survey for a user
    GET /api/surveys/fitness/{user_id}
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # Users can view their own survey
        # Coaches can view surveys of their assigned clients (will add this check in Phase 2)
        # Admins can view any survey
        if current_user_id != user_id and current_user.role != 'admin':
            return error_response('Unauthorized to view this survey', 403)

        survey = FitnessSurvey.query.filter_by(user_id=user_id).first()

        if not survey:
            return error_response('Fitness survey not found', 404)

        return success_response(survey.to_dict(), 'Fitness survey retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve fitness survey', 500, str(e))


@surveys_bp.route('/fitness/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_fitness_survey(user_id):
    """
    Delete fitness survey
    DELETE /api/surveys/fitness/{user_id}
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Users can only delete their own survey
        if current_user_id != user_id:
            return error_response('Unauthorized to delete this survey', 403)

        survey = FitnessSurvey.query.filter_by(user_id=user_id).first()

        if not survey:
            return error_response('Fitness survey not found', 404)

        db.session.delete(survey)
        db.session.commit()

        return success_response(None, 'Fitness survey deleted successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete fitness survey', 500, str(e))


@surveys_bp.route('/fitness', methods=['GET'])
@jwt_required()
def get_my_fitness_survey():
    """
    Get current user's fitness survey
    GET /api/surveys/fitness
    """
    try:
        user_id = int(get_jwt_identity())
        survey = FitnessSurvey.query.filter_by(user_id=user_id).first()

        if not survey:
            return error_response('Fitness survey not found', 404)

        return success_response(survey.to_dict(), 'Fitness survey retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve fitness survey', 500, str(e))
