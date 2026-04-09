from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProfile, FitnessSurvey, RoleChangeRequest, CoachRelationship, WorkoutPlan, Review
from utils.validators import is_valid_email, is_valid_password, is_valid_role, is_valid_fitness_level
from utils.helpers import success_response, error_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def _admin_user_dict(user):
    """Serialize a user for admin views, including profile and fitness survey."""
    data = user.to_dict(include_profile=True)
    data['fitness_survey'] = user.fitness_survey.to_dict() if user.fitness_survey else None
    return data

def admin_required(fn):
    """Decorator to require admin role"""
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return error_response('Admin access required', 403)
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return success_response({
            'users': [_admin_user_dict(u) for u in users]
        }, 'Users retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve users', 500, str(e))

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """
    Create a new user (admin only)
    POST /api/admin/users
    Body: {
      email, password,
      role?,                 # client|coach|both|admin
      first_name?, last_name?, bio?, phone?,
      fitness_survey?: { weight?, age?, fitness_level?, goals? }
    }
    """
    try:
        data = request.get_json() or {}

        if 'email' not in data or 'password' not in data:
            return error_response('Email and password are required', 400)

        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not is_valid_email(email):
            return error_response('Invalid email format', 400)

        if User.query.filter_by(email=email).first():
            return error_response('Email already registered', 409)

        is_valid, pw_message = is_valid_password(password)
        if not is_valid:
            return error_response(pw_message, 400)

        role = data.get('role')
        if role and not is_valid_role(role):
            return error_response('Invalid role. Must be: client, coach, both, or admin', 400)

        # Create user
        user = User(email=email, role=role)
        user.set_password(password)

        # Create profile (always create, even if empty, to mirror signup flow)
        profile = UserProfile(
            user=user,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            bio=data.get('bio'),
            phone=data.get('phone'),
        )

        db.session.add(user)
        db.session.add(profile)

        # Optional fitness survey
        survey_data = data.get('fitness_survey') or {}
        if any(survey_data.get(k) not in (None, '') for k in ('weight', 'age', 'fitness_level', 'goals')):
            fitness_level = survey_data.get('fitness_level')
            if fitness_level and not is_valid_fitness_level(fitness_level):
                db.session.rollback()
                return error_response('Invalid fitness level. Must be: beginner, intermediate, or advanced', 400)

            survey = FitnessSurvey(
                user=user,
                weight=survey_data.get('weight') or None,
                age=survey_data.get('age') or None,
                fitness_level=fitness_level or None,
                goals=survey_data.get('goals') or None,
            )
            db.session.add(survey)

        db.session.commit()

        return success_response(
            _admin_user_dict(user),
            'User created successfully',
            201
        )

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to create user', 500, str(e))

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    Update an existing user's information (admin only)
    PUT /api/admin/users/<user_id>
    Body: {
      email?, password?, role?, status?,
      first_name?, last_name?, phone?, bio?,
      fitness_survey?: { weight?, age?, fitness_level?, goals? }
    }
    All fields optional. Only provided fields will be updated.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        data = request.get_json() or {}

        # --- User account fields ---
        if 'email' in data and data['email'] is not None:
            new_email = (data['email'] or '').strip().lower()
            if not new_email:
                return error_response('Email cannot be empty', 400)
            if not is_valid_email(new_email):
                return error_response('Invalid email format', 400)
            if new_email != user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing and existing.id != user.id:
                    return error_response('Email already registered', 409)
                user.email = new_email

        if 'password' in data and data['password']:
            is_valid, pw_message = is_valid_password(data['password'])
            if not is_valid:
                return error_response(pw_message, 400)
            user.set_password(data['password'])

        if 'role' in data and data['role'] is not None:
            if not is_valid_role(data['role']):
                return error_response('Invalid role. Must be: client, coach, both, or admin', 400)
            user.role = data['role']

        if 'status' in data and data['status'] is not None:
            if data['status'] not in ('active', 'disabled'):
                return error_response("Invalid status. Must be 'active' or 'disabled'", 400)
            # Prevent admin from disabling themselves
            current_user_id = int(get_jwt_identity())
            if user.id == current_user_id and data['status'] == 'disabled':
                return error_response('You cannot disable your own account', 400)
            user.status = data['status']

        # --- Profile fields ---
        profile_keys = ('first_name', 'last_name', 'phone', 'bio')
        if any(k in data for k in profile_keys):
            profile = user.profile
            if not profile:
                profile = UserProfile(user=user)
                db.session.add(profile)
            for key in profile_keys:
                if key in data:
                    setattr(profile, key, data[key])

        # --- Fitness survey ---
        if 'fitness_survey' in data and data['fitness_survey'] is not None:
            survey_data = data['fitness_survey'] or {}
            fitness_level = survey_data.get('fitness_level')
            if 'fitness_level' in survey_data and fitness_level and not is_valid_fitness_level(fitness_level):
                return error_response('Invalid fitness level. Must be: beginner, intermediate, or advanced', 400)

            survey = user.fitness_survey
            if not survey:
                survey = FitnessSurvey(user=user)
                db.session.add(survey)

            if 'weight' in survey_data:
                survey.weight = survey_data['weight'] if survey_data['weight'] not in ('', None) else None
            if 'age' in survey_data:
                survey.age = survey_data['age'] if survey_data['age'] not in ('', None) else None
            if 'fitness_level' in survey_data:
                survey.fitness_level = fitness_level if fitness_level else None
            if 'goals' in survey_data:
                survey.goals = survey_data['goals'] if survey_data['goals'] not in ('', None) else None

        db.session.commit()

        return success_response(
            _admin_user_dict(user),
            'User updated successfully',
            200
        )

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update user', 500, str(e))

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only). Admins cannot delete their own account."""
    try:
        current_user_id = int(get_jwt_identity())
        if current_user_id == user_id:
            return error_response('You cannot delete your own account', 400)

        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        db.session.delete(user)
        db.session.commit()

        return success_response(None, 'User deleted successfully', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete user', 500, str(e))

@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@admin_required
def update_user_status(user_id):
    """Update user status (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        data = request.get_json()
        if 'status' in data:
            user.status = data['status']

        db.session.commit()
        return success_response(user.to_dict(), 'User status updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update user status', 500, str(e))

@admin_bp.route('/role-requests', methods=['GET'])
@admin_required
def list_role_requests():
    """
    List role change requests (admin only).
    GET /api/admin/role-requests?status=pending|approved|rejected|all
    Default: pending
    """
    try:
        status_filter = request.args.get('status', 'pending')
        query = RoleChangeRequest.query
        if status_filter != 'all':
            if status_filter not in ('pending', 'approved', 'rejected'):
                return error_response("Invalid status filter", 400)
            query = query.filter_by(status=status_filter)

        requests_list = query.order_by(RoleChangeRequest.created_at.desc()).all()

        return success_response({
            'role_requests': [r.to_dict(include_user=True) for r in requests_list]
        }, 'Role change requests retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve role change requests', 500, str(e))


@admin_bp.route('/role-requests/<int:request_id>', methods=['PATCH'])
@admin_required
def respond_to_role_request(request_id):
    """
    Approve or reject a role change request (admin only).
    PATCH /api/admin/role-requests/<request_id>
    Body: {status: 'approved' | 'rejected', admin_notes?: string}
    On approval, the user's role is updated to the requested role.
    """
    try:
        current_user_id = int(get_jwt_identity())
        req = RoleChangeRequest.query.get(request_id)
        if not req:
            return error_response('Role change request not found', 404)

        if req.status != 'pending':
            return error_response(
                f'This request has already been {req.status}',
                400
            )

        data = request.get_json() or {}
        new_status = data.get('status')
        if new_status not in ('approved', 'rejected'):
            return error_response(
                "Invalid status. Must be 'approved' or 'rejected'",
                400
            )

        req.status = new_status
        req.admin_notes = (data.get('admin_notes') or '').strip() or None
        req.reviewed_at = datetime.utcnow()
        req.reviewed_by = current_user_id

        # On approval, actually update the user's role
        if new_status == 'approved':
            target_user = req.user
            if not target_user:
                db.session.rollback()
                return error_response('Target user no longer exists', 404)
            target_user.role = req.requested_role

        db.session.commit()

        return success_response(
            req.to_dict(include_user=True),
            f'Role change request {new_status}',
            200
        )
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to respond to role change request', 500, str(e))


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_platform_stats():
    """Get platform statistics (admin only)"""
    try:
        total_users = User.query.count()
        total_coaches = User.query.filter(User.role.in_(['coach', 'both'])).count()
        total_clients = User.query.filter(User.role.in_(['client', 'both'])).count()
        active_relationships = CoachRelationship.query.filter_by(status='active').count()
        total_workout_plans = WorkoutPlan.query.count()

        return success_response({
            'total_users': total_users,
            'total_coaches': total_coaches,
            'total_clients': total_clients,
            'active_relationships': active_relationships,
            'total_workout_plans': total_workout_plans
        }, 'Platform stats retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve stats', 500, str(e))
