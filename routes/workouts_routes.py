from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Exercise, WorkoutPlan, WorkoutDay, PlanExercise, WorkoutLog, ExerciseLog, CoachRelationship
from utils.helpers import success_response, error_response
from datetime import datetime, date
from sqlalchemy import or_, and_

workouts_bp = Blueprint('workouts', __name__, url_prefix='/api/workouts')

# ============================================
# Exercise Management
# ============================================

@workouts_bp.route('/exercises', methods=['GET'])
@jwt_required()
def get_exercises():
    """
    Get exercise database
    GET /api/workouts/exercises?category=strength&muscle_group=chest&search=bench
    """
    try:
        user_id = int(get_jwt_identity())

        # Build query
        query = Exercise.query

        # Filter by category
        category = request.args.get('category')
        if category:
            query = query.filter_by(category=category)

        # Filter by muscle group
        muscle_group = request.args.get('muscle_group')
        if muscle_group:
            query = query.filter_by(muscle_group=muscle_group)

        # Filter by difficulty
        difficulty = request.args.get('difficulty')
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        # Search by name
        search = request.args.get('search')
        if search:
            query = query.filter(Exercise.name.ilike(f'%{search}%'))

        # Only show public exercises or user's own exercises
        query = query.filter(
            or_(
                Exercise.is_public == True,
                Exercise.created_by == user_id
            )
        )

        exercises = query.all()

        return success_response({
            'exercises': [ex.to_dict() for ex in exercises]
        }, 'Exercises retrieved successfully', 200)

    except Exception as e:
        import traceback
        print(f"\n===== ERROR in GET /exercises =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response('Failed to retrieve exercises', 500, str(e))


@workouts_bp.route('/exercises', methods=['POST'])
@jwt_required()
def create_exercise():
    """
    Create a custom exercise
    POST /api/workouts/exercises
    Body: {name, description, category, muscle_group, equipment, difficulty, instructions, is_public}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'name' not in data:
            return error_response('Exercise name is required', 400)

        exercise = Exercise(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            muscle_group=data.get('muscle_group'),
            equipment=data.get('equipment'),
            difficulty=data.get('difficulty'),
            video_url=data.get('video_url'),
            instructions=data.get('instructions'),
            created_by=user_id,
            is_public=data.get('is_public', False)
        )

        db.session.add(exercise)
        db.session.commit()

        return success_response(exercise.to_dict(), 'Exercise created successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create exercise', 500, str(e))


# ============================================
# Workout Plan Management
# ============================================

@workouts_bp.route('/plans', methods=['GET'])
@jwt_required()
def get_workout_plans():
    """
    Get workout plans for the current user (as client or coach)
    GET /api/workouts/plans?role=coach (returns plans created by coach)
    GET /api/workouts/plans?role=client (returns plans assigned to client)
    """
    try:
        user_id = int(get_jwt_identity())
        role = request.args.get('role', 'client')

        if role == 'coach':
            plans = WorkoutPlan.query.filter_by(coach_id=user_id).all()
        else:
            plans = WorkoutPlan.query.filter_by(client_id=user_id).all()

        # Safely serialize plans with error handling
        plans_data = []
        for plan in plans:
            try:
                plans_data.append(plan.to_dict())
            except Exception as plan_error:
                print(f"Error serializing plan {plan.id}: {str(plan_error)}")
                continue

        return success_response({
            'plans': plans_data
        }, 'Workout plans retrieved successfully', 200)

    except Exception as e:
        print(f"Error retrieving workout plans: {str(e)}")
        return error_response('Failed to retrieve workout plans', 500, str(e))


@workouts_bp.route('/plans/<int:plan_id>', methods=['GET'])
@jwt_required()
def get_workout_plan(plan_id):
    """
    Get a specific workout plan with all days and exercises
    GET /api/workouts/plans/{plan_id}
    """
    try:
        user_id = int(get_jwt_identity())

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response('Workout plan not found', 404)

        # Verify user has access
        if plan.coach_id != user_id and plan.client_id != user_id:
            return error_response('Unauthorized to access this workout plan', 403)

        return success_response(plan.to_dict(include_days=True), 'Workout plan retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve workout plan', 500, str(e))


@workouts_bp.route('/plans', methods=['POST'])
@jwt_required()
def create_workout_plan():
    """
    Create a workout plan (coach only)
    POST /api/workouts/plans
    Body: {name, description, client_id, start_date, end_date, days: [...]}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'name' not in data or 'client_id' not in data:
            return error_response('name and client_id are required', 400)

        client_id = data['client_id']

        # Verify coach-client relationship exists
        relationship = CoachRelationship.query.filter_by(
            coach_id=user_id,
            client_id=client_id,
            status='active'
        ).first()

        if not relationship:
            return error_response('No active relationship with this client', 403)

        # Create plan
        plan = WorkoutPlan(
            name=data['name'],
            description=data.get('description'),
            coach_id=user_id,
            client_id=client_id,
            start_date=datetime.fromisoformat(data['start_date']).date() if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']).date() if data.get('end_date') else None
        )

        db.session.add(plan)
        db.session.flush()  # Get plan.id before adding days

        # Add workout days if provided
        if 'days' in data and isinstance(data['days'], list):
            for day_data in data['days']:
                day = WorkoutDay(
                    plan_id=plan.id,
                    name=day_data['name'],
                    day_number=day_data.get('day_number'),
                    notes=day_data.get('notes')
                )
                db.session.add(day)
                db.session.flush()  # Get day.id before adding exercises

                # Add exercises to the day if provided
                if 'exercises' in day_data and isinstance(day_data['exercises'], list):
                    for ex_data in day_data['exercises']:
                        plan_exercise = PlanExercise(
                            workout_day_id=day.id,
                            exercise_id=ex_data['exercise_id'],
                            order=ex_data.get('order'),
                            sets=ex_data.get('sets'),
                            reps=ex_data.get('reps'),
                            duration_minutes=ex_data.get('duration_minutes'),
                            rest_seconds=ex_data.get('rest_seconds'),
                            weight=ex_data.get('weight'),
                            notes=ex_data.get('notes')
                        )
                        db.session.add(plan_exercise)

        db.session.commit()

        return success_response(plan.to_dict(include_days=True), 'Workout plan created successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create workout plan', 500, str(e))


@workouts_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_workout_plan(plan_id):
    """
    Update a workout plan (coach only)
    PUT /api/workouts/plans/{plan_id}
    Body: {name, description, start_date, end_date, status}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response('Workout plan not found', 404)

        # Only coach can update
        if plan.coach_id != user_id:
            return error_response('Only the coach can update this plan', 403)

        # Update fields
        if 'name' in data:
            plan.name = data['name']
        if 'description' in data:
            plan.description = data['description']
        if 'start_date' in data:
            plan.start_date = datetime.fromisoformat(data['start_date']).date() if data['start_date'] else None
        if 'end_date' in data:
            plan.end_date = datetime.fromisoformat(data['end_date']).date() if data['end_date'] else None
        if 'status' in data:
            plan.status = data['status']

        db.session.commit()

        return success_response(plan.to_dict(include_days=True), 'Workout plan updated successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update workout plan', 500, str(e))


@workouts_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_workout_plan(plan_id):
    """
    Delete a workout plan (coach only)
    DELETE /api/workouts/plans/{plan_id}
    """
    try:
        user_id = int(get_jwt_identity())

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response('Workout plan not found', 404)

        # Only coach can delete
        if plan.coach_id != user_id:
            return error_response('Only the coach can delete this plan', 403)

        db.session.delete(plan)
        db.session.commit()

        return success_response(None, 'Workout plan deleted successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete workout plan', 500, str(e))


# ============================================
# Workout Logging
# ============================================

@workouts_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_workout_logs():
    """
    Get workout logs for the current user
    GET /api/workouts/logs?start_date=2024-01-01&end_date=2024-12-31
    """
    try:
        user_id = int(get_jwt_identity())

        # Build query
        query = WorkoutLog.query.filter_by(client_id=user_id)

        # Filter by date range
        start_date = request.args.get('start_date')
        if start_date:
            query = query.filter(WorkoutLog.date >= datetime.fromisoformat(start_date).date())

        end_date = request.args.get('end_date')
        if end_date:
            query = query.filter(WorkoutLog.date <= datetime.fromisoformat(end_date).date())

        logs = query.order_by(WorkoutLog.date.desc()).all()

        return success_response({
            'logs': [log.to_dict(include_exercises=True) for log in logs]
        }, 'Workout logs retrieved successfully', 200)

    except Exception as e:
        import traceback
        print(f"\n===== ERROR in GET /logs =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response('Failed to retrieve workout logs', 500, str(e))


@workouts_bp.route('/logs', methods=['POST'])
@jwt_required()
def create_workout_log():
    """
    Log a completed workout
    POST /api/workouts/logs
    Body: {plan_id, workout_day_id, date, duration_minutes, notes, rating, exercises: [...]}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'date' not in data:
            return error_response('date is required', 400)

        # Convert empty strings to None for foreign keys
        plan_id = data.get('plan_id') or None
        workout_day_id = data.get('workout_day_id') or None

        # Convert duration_minutes to int if provided
        duration_minutes = None
        if data.get('duration_minutes'):
            try:
                duration_minutes = int(data['duration_minutes'])
            except (ValueError, TypeError):
                duration_minutes = None

        # Convert rating to int if provided
        rating = None
        if data.get('rating'):
            try:
                rating = int(data['rating'])
            except (ValueError, TypeError):
                rating = None

        # Create workout log
        log = WorkoutLog(
            client_id=user_id,
            plan_id=plan_id,
            workout_day_id=workout_day_id,
            date=datetime.fromisoformat(data['date']).date(),
            duration_minutes=duration_minutes,
            notes=data.get('notes'),
            rating=rating,
            completed=data.get('completed', True)
        )

        db.session.add(log)
        db.session.flush()  # Get log.id

        # Add exercise logs if provided
        if 'exercises' in data and isinstance(data['exercises'], list):
            for ex_data in data['exercises']:
                exercise_log = ExerciseLog(
                    workout_log_id=log.id,
                    exercise_id=ex_data['exercise_id'],
                    sets_completed=ex_data.get('sets_completed'),
                    reps_completed=ex_data.get('reps_completed'),
                    weight_used=ex_data.get('weight_used'),
                    duration_minutes=ex_data.get('duration_minutes'),
                    notes=ex_data.get('notes')
                )
                db.session.add(exercise_log)

        db.session.commit()

        return success_response(log.to_dict(include_exercises=True), 'Workout logged successfully', 201)

    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"\n===== ERROR in POST /logs =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response('Failed to log workout', 500, str(e))


@workouts_bp.route('/logs/<int:log_id>', methods=['PUT'])
@jwt_required()
def update_workout_log(log_id):
    """
    Update a workout log
    PUT /api/workouts/logs/{log_id}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        log = WorkoutLog.query.get(log_id)
        if not log:
            return error_response('Workout log not found', 404)

        # Only owner can update
        if log.client_id != user_id:
            return error_response('Unauthorized to update this workout log', 403)

        # Update fields
        if 'duration_minutes' in data:
            log.duration_minutes = data['duration_minutes']
        if 'notes' in data:
            log.notes = data['notes']
        if 'rating' in data:
            log.rating = data['rating']
        if 'completed' in data:
            log.completed = data['completed']

        db.session.commit()

        return success_response(log.to_dict(include_exercises=True), 'Workout log updated successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update workout log', 500, str(e))


@workouts_bp.route('/logs/<int:log_id>', methods=['DELETE'])
@jwt_required()
def delete_workout_log(log_id):
    """
    Delete a workout log
    DELETE /api/workouts/logs/{log_id}
    """
    try:
        user_id = int(get_jwt_identity())

        log = WorkoutLog.query.get(log_id)
        if not log:
            return error_response('Workout log not found', 404)

        # Only owner can delete
        if log.client_id != user_id:
            return error_response('Unauthorized to delete this workout log', 403)

        db.session.delete(log)
        db.session.commit()

        return success_response(None, 'Workout log deleted successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete workout log', 500, str(e))


# ============================================
# Calendar & Stats
# ============================================

@workouts_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_workout_calendar():
    """
    Get workout calendar for a month
    GET /api/workouts/calendar?year=2024&month=1
    """
    try:
        user_id = int(get_jwt_identity())

        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)

        # Get first and last day of the month
        from calendar import monthrange
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # Get workout logs for the month
        logs = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= first_day,
            WorkoutLog.date <= last_day
        ).all()

        # Get active workout plans
        plans = WorkoutPlan.query.filter_by(
            client_id=user_id,
            status='active'
        ).all()

        return success_response({
            'logs': [log.to_dict() for log in logs],
            'plans': [plan.to_dict() for plan in plans]
        }, 'Calendar data retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve calendar data', 500, str(e))


@workouts_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_workout_stats():
    """
    Get workout statistics
    GET /api/workouts/stats?period=30 (last 30 days)
    """
    try:
        user_id = int(get_jwt_identity())
        period = request.args.get('period', 30, type=int)

        # Calculate date range
        end_date = date.today()
        from datetime import timedelta
        start_date = end_date - timedelta(days=period)

        # Get logs for the period
        logs = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date,
            WorkoutLog.date <= end_date,
            WorkoutLog.completed == True
        ).all()

        # Calculate stats
        total_workouts = len(logs)
        total_duration = sum(log.duration_minutes or 0 for log in logs)
        avg_rating = sum(log.rating or 0 for log in logs) / total_workouts if total_workouts > 0 else 0

        return success_response({
            'period_days': period,
            'total_workouts': total_workouts,
            'total_duration_minutes': total_duration,
            'average_duration_minutes': total_duration / total_workouts if total_workouts > 0 else 0,
            'average_rating': round(avg_rating, 1),
            'workout_frequency_per_week': round((total_workouts / period) * 7, 1)
        }, 'Workout statistics retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve workout statistics', 500, str(e))
