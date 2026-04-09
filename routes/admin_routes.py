from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models import (
    db,
    User,
    UserProfile,
    FitnessSurvey,
    RoleChangeRequest,
    CoachRelationship,
    WorkoutPlan,
    Review,
    CoachApplication,
    ModerationReport,
    Exercise,
    ClientRequest,
    PaymentRecord,
    WorkoutTemplate,
)
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

        user = User(email=email, role=role)
        user.set_password(password)

        profile = UserProfile(
            user=user,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            bio=data.get('bio'),
            phone=data.get('phone'),
        )

        db.session.add(user)
        db.session.add(profile)

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

        return success_response(_admin_user_dict(user), 'User created successfully', 201)

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
        open_reports = ModerationReport.query.filter_by(status='open').count()
        pending_coach_applications = CoachApplication.query.filter_by(status='pending').count()
        total_revenue = db.session.query(func.sum(PaymentRecord.amount)).filter_by(status='completed').scalar() or 0

        return success_response({
            'total_users': total_users,
            'total_coaches': total_coaches,
            'total_clients': total_clients,
            'active_relationships': active_relationships,
            'total_workout_plans': total_workout_plans
            ,
            'open_reports': open_reports,
            'pending_coach_applications': pending_coach_applications,
            'total_revenue': float(total_revenue)
        }, 'Platform stats retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve stats', 500, str(e))


@admin_bp.route('/coach-applications', methods=['GET'])
@admin_required
def get_coach_applications():
    """List coach applications"""
    try:
        applications = CoachApplication.query.order_by(CoachApplication.submitted_at.desc()).all()
        return success_response({
            'applications': [application.to_dict() for application in applications]
        }, 'Coach applications retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve coach applications', 500, str(e))


@admin_bp.route('/coach-applications/<int:application_id>', methods=['PATCH'])
@admin_required
def review_coach_application(application_id):
    """Approve or deny coach applications"""
    try:
        admin_id = int(get_jwt_identity())
        application = CoachApplication.query.get(application_id)
        if not application:
            return error_response('Application not found', 404)

        data = request.get_json() or {}
        status = data.get('status')
        if status not in ['approved', 'denied']:
            return error_response('Invalid status', 400)

        application.status = status
        application.reviewed_by = admin_id
        application.reviewed_at = datetime.utcnow()
        if 'notes' in data:
            application.notes = data['notes']
        db.session.commit()
        return success_response(application.to_dict(), f'Coach application {status}', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to review coach application', 500, str(e))


@admin_bp.route('/reports', methods=['GET'])
@admin_required
def get_reports():
    """List moderation reports"""
    try:
        reports = ModerationReport.query.order_by(ModerationReport.created_at.desc()).all()
        return success_response({
            'reports': [report.to_dict() for report in reports]
        }, 'Reports retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve reports', 500, str(e))


@admin_bp.route('/reports/<int:report_id>', methods=['PATCH'])
@admin_required
def update_report(report_id):
    """Update report review status"""
    try:
        admin_id = int(get_jwt_identity())
        report = ModerationReport.query.get(report_id)
        if not report:
            return error_response('Report not found', 404)

        data = request.get_json() or {}
        status = data.get('status')
        if status not in ['reviewed', 'resolved', 'dismissed']:
            return error_response('Invalid status', 400)

        report.status = status
        report.reviewed_by = admin_id
        report.reviewed_at = datetime.utcnow()
        db.session.commit()
        return success_response(report.to_dict(), 'Report updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update report', 500, str(e))


@admin_bp.route('/exercises', methods=['GET', 'POST'])
@admin_required
def manage_exercises():
    """Admin exercise inventory management"""
    try:
        if request.method == 'GET':
            exercises = Exercise.query.order_by(Exercise.created_at.desc()).all()
            return success_response({'exercises': [exercise.to_dict() for exercise in exercises]}, 'Exercises retrieved', 200)

        data = request.get_json() or {}
        exercise = Exercise(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            muscle_group=data.get('muscle_group'),
            equipment=data.get('equipment'),
            difficulty=data.get('difficulty'),
            instructions=data.get('instructions'),
            is_public=data.get('is_public', True)
        )
        db.session.add(exercise)
        db.session.commit()
        return success_response(exercise.to_dict(), 'Exercise created', 201)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to manage exercises', 500, str(e))


@admin_bp.route('/exercises/<int:exercise_id>', methods=['PUT', 'DELETE'])
@admin_required
def manage_exercise(exercise_id):
    """Admin update/delete exercise"""
    try:
        exercise = Exercise.query.get(exercise_id)
        if not exercise:
            return error_response('Exercise not found', 404)

        if request.method == 'DELETE':
            db.session.delete(exercise)
            db.session.commit()
            return success_response(None, 'Exercise deleted', 200)

        data = request.get_json() or {}
        for field in ['name', 'description', 'category', 'muscle_group', 'equipment', 'difficulty', 'instructions']:
            if field in data:
                setattr(exercise, field, data[field])
        if 'is_public' in data:
            exercise.is_public = data['is_public']
        db.session.commit()
        return success_response(exercise.to_dict(), 'Exercise updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to manage exercise', 500, str(e))


@admin_bp.route('/requests', methods=['GET'])
@admin_required
def get_requests():
    """List coach request statuses"""
    try:
        requests = ClientRequest.query.order_by(ClientRequest.requested_at.desc()).all()
        return success_response({
            'requests': [item.to_dict() for item in requests]
        }, 'Requests retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve requests', 500, str(e))


@admin_bp.route('/requests/<int:request_id>', methods=['PATCH'])
@admin_required
def update_request(request_id):
    """Admin override for coach request status"""
    try:
        request_item = ClientRequest.query.get(request_id)
        if not request_item:
            return error_response('Request not found', 404)

        data = request.get_json() or {}
        status = data.get('status')
        if status not in ['pending', 'accepted', 'denied']:
            return error_response('Invalid status', 400)

        request_item.status = status
        request_item.responded_at = datetime.utcnow()
        if status == 'accepted':
            relationship = CoachRelationship.query.filter_by(
                client_id=request_item.client_id,
                coach_id=request_item.coach_id,
                status='active'
            ).first()
            if not relationship:
                db.session.add(CoachRelationship(
                    client_id=request_item.client_id,
                    coach_id=request_item.coach_id,
                    status='active'
                ))
        db.session.commit()
        return success_response(request_item.to_dict(), 'Request updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update request', 500, str(e))


@admin_bp.route('/payment-analytics', methods=['GET'])
@admin_required
def payment_analytics():
    """Return payment analytics"""
    try:
        total_revenue = db.session.query(func.sum(PaymentRecord.amount)).filter_by(status='completed').scalar() or 0
        payment_count = PaymentRecord.query.count()
        payments = PaymentRecord.query.order_by(PaymentRecord.created_at.desc()).limit(20).all()
        return success_response({
            'total_revenue': float(total_revenue),
            'payment_count': payment_count,
            'payments': [payment.to_dict() for payment in payments]
        }, 'Payment analytics retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve payment analytics', 500, str(e))


@admin_bp.route('/templates', methods=['GET', 'PATCH'])
@admin_required
def manage_templates():
    """View and approve workout templates"""
    try:
        if request.method == 'GET':
            templates = WorkoutTemplate.query.order_by(WorkoutTemplate.created_at.desc()).all()
            return success_response({'templates': [template.to_dict() for template in templates]}, 'Templates retrieved', 200)

        data = request.get_json() or {}
        template = WorkoutTemplate.query.get(data.get('template_id'))
        if not template:
            return error_response('Template not found', 404)
        if 'approved' in data:
            template.approved = bool(data['approved'])
        if 'is_public' in data:
            template.is_public = bool(data['is_public'])
        db.session.commit()
        return success_response(template.to_dict(), 'Template updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to manage templates', 500, str(e))
