from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import (
    db,
    User,
    UserProfile,
    RoleChangeRequest,
    FitnessSurvey,
    CoachSurvey,
    CoachSpecialization,
    CoachAvailability,
    CoachPricing,
    ClientRequest,
    CoachApplication,
    ModerationReport,
    CoachRelationship,
    Review,
    ChatMessage,
    Exercise,
    WorkoutPlan,
    WorkoutTemplate,
    WorkoutPlanAssignment,
    CalendarNote,
    WorkoutLog,
    ExerciseLog,
    MealLog,
    BodyMetric,
    WellnessLog,
    DailyMetric,
    MealPlan,
    Notification,
    PaymentRecord,
)
from utils.validators import is_valid_role
from utils.helpers import success_response, error_response
from middleware.auth_middleware import require_role

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


def _delete_user_data(user_id):
    """Delete all rows owned by or pointing at a user before removing the user row."""
    workout_plan_ids = [plan.id for plan in WorkoutPlan.query.filter(
        (WorkoutPlan.client_id == user_id) | (WorkoutPlan.coach_id == user_id)
    ).all()]
    workout_log_ids = [log.id for log in WorkoutLog.query.filter_by(client_id=user_id).all()]
    relationship_ids = [rel.id for rel in CoachRelationship.query.filter(
        (CoachRelationship.client_id == user_id) | (CoachRelationship.coach_id == user_id)
    ).all()]
    message_relationship_ids = [msg.relationship_id for msg in ChatMessage.query.filter_by(sender_id=user_id).all() if msg.relationship_id]
    report_relationship_ids = [report.relationship_id for report in ModerationReport.query.filter_by(reporter_id=user_id).all() if report.relationship_id]

    if workout_log_ids:
        ExerciseLog.query.filter(ExerciseLog.workout_log_id.in_(workout_log_ids)).delete(synchronize_session=False)
        WorkoutLog.query.filter(WorkoutLog.id.in_(workout_log_ids)).delete(synchronize_session=False)

    if workout_plan_ids:
        WorkoutLog.query.filter(WorkoutLog.plan_id.in_(workout_plan_ids)).delete(synchronize_session=False)
        WorkoutPlanAssignment.query.filter(WorkoutPlanAssignment.plan_id.in_(workout_plan_ids)).delete(synchronize_session=False)
        CalendarNote.query.filter(CalendarNote.user_id == user_id).delete(synchronize_session=False)
        WorkoutPlan.query.filter(WorkoutPlan.id.in_(workout_plan_ids)).delete(synchronize_session=False)

    all_relationship_ids = set(relationship_ids) | set(message_relationship_ids) | set(report_relationship_ids)
    if all_relationship_ids:
        ChatMessage.query.filter(ChatMessage.relationship_id.in_(all_relationship_ids)).delete(synchronize_session=False)
        ModerationReport.query.filter(ModerationReport.relationship_id.in_(all_relationship_ids)).delete(synchronize_session=False)
        CoachRelationship.query.filter(CoachRelationship.id.in_(all_relationship_ids)).delete(synchronize_session=False)

    Review.query.filter((Review.client_id == user_id) | (Review.coach_id == user_id)).delete(synchronize_session=False)
    ModerationReport.query.filter((ModerationReport.reporter_id == user_id) | (ModerationReport.reported_user_id == user_id)).delete(synchronize_session=False)
    ChatMessage.query.filter(ChatMessage.sender_id == user_id).delete(synchronize_session=False)

    Exercise.query.filter(Exercise.created_by == user_id).delete(synchronize_session=False)
    WorkoutTemplate.query.filter(WorkoutTemplate.created_by == user_id).delete(synchronize_session=False)

    Notification.query.filter(Notification.user_id == user_id).delete(synchronize_session=False)
    PaymentRecord.query.filter(PaymentRecord.payer_id == user_id).delete(synchronize_session=False)
    MealLog.query.filter(MealLog.user_id == user_id).delete(synchronize_session=False)
    BodyMetric.query.filter(BodyMetric.user_id == user_id).delete(synchronize_session=False)
    WellnessLog.query.filter(WellnessLog.user_id == user_id).delete(synchronize_session=False)
    DailyMetric.query.filter(DailyMetric.user_id == user_id).delete(synchronize_session=False)
    MealPlan.query.filter(MealPlan.user_id == user_id).delete(synchronize_session=False)

    ClientRequest.query.filter((ClientRequest.client_id == user_id) | (ClientRequest.coach_id == user_id)).delete(synchronize_session=False)
    CoachApplication.query.filter(CoachApplication.user_id == user_id).delete(synchronize_session=False)
    CoachSurvey.query.filter(CoachSurvey.user_id == user_id).delete(synchronize_session=False)
    CoachSpecialization.query.filter(CoachSpecialization.coach_id == user_id).delete(synchronize_session=False)
    CoachAvailability.query.filter(CoachAvailability.coach_id == user_id).delete(synchronize_session=False)
    CoachPricing.query.filter(CoachPricing.coach_id == user_id).delete(synchronize_session=False)

    RoleChangeRequest.query.filter(RoleChangeRequest.user_id == user_id).delete(synchronize_session=False)
    FitnessSurvey.query.filter(FitnessSurvey.user_id == user_id).delete(synchronize_session=False)
    UserProfile.query.filter(UserProfile.user_id == user_id).delete(synchronize_session=False)

    db.session.flush()
    db.session.expunge_all()

@users_bp.route('/<int:user_id>/role', methods=['PATCH'])
@jwt_required()
def update_user_role(user_id):
    """
    Update user role (UC 1.4)
    PATCH /api/users/{id}/role
    Body: {role: 'client' | 'coach' | 'both'}
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Users can only update their own role
        if current_user_id != user_id:
            return error_response('Unauthorized to update this user role', 403)

        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        data = request.get_json()
        if not data or 'role' not in data:
            return error_response('Role is required', 400)

        role = data['role']

        # Validate role
        if not is_valid_role(role):
            return error_response('Invalid role. Must be: client, coach, both, or admin', 400)

        # Admin role cannot be self-assigned
        if role == 'admin':
            return error_response('Admin role cannot be self-assigned', 403)

        # Clients upgrading to coach/both must go through the admin approval flow
        if user.role == 'client' and role in ('coach', 'both'):
            return error_response(
                'Submit a role change request for admin approval to become a coach',
                403
            )

        # Update role
        user.role = role
        db.session.commit()

        return success_response(user.to_dict(include_profile=True), 'Role updated successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update role', 500, str(e))


@users_bp.route('/<int:user_id>/profile', methods=['GET'])
@jwt_required()
def get_user_profile(user_id):
    """
    Get user profile
    GET /api/users/{id}/profile
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        return success_response({
            'user': user.to_dict(include_profile=True)
        }, 'Profile retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve profile', 500, str(e))


@users_bp.route('/<int:user_id>/profile', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    """
    Update user profile
    PUT /api/users/{id}/profile
    Body: {first_name, last_name, bio, phone}
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Users can only update their own profile
        if current_user_id != user_id:
            return error_response('Unauthorized to update this profile', 403)

        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        # Get or create profile
        profile = user.profile
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        data = request.get_json()

        # Update profile fields
        if 'first_name' in data:
            profile.first_name = data['first_name']
        if 'last_name' in data:
            profile.last_name = data['last_name']
        if 'bio' in data:
            profile.bio = data['bio']
        if 'phone' in data:
            profile.phone = data['phone']

        db.session.commit()

        return success_response(user.to_dict(include_profile=True), 'Profile updated successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update profile', 500, str(e))


@users_bp.route('', methods=['GET'])
@require_role('admin')
def get_all_users():
    """
    Get all users (Admin only)
    GET /api/users?page=1&per_page=20&search=query
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)

        query = User.query

        # Search by email or name
        if search:
            search_term = f'%{search}%'
            query = query.join(UserProfile).filter(
                db.or_(
                    User.email.ilike(search_term),
                    UserProfile.first_name.ilike(search_term),
                    UserProfile.last_name.ilike(search_term)
                )
            )

        # Paginate
        paginated = query.paginate(page=page, per_page=min(per_page, 100), error_out=False)

        return success_response({
            'users': [user.to_dict(include_profile=True) for user in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'per_page': per_page
        }, 'Users retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve users', 500, str(e))


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user_account(user_id):
    """
    Delete user account and all associated data (UC 7.5)
    DELETE /api/users/{id}
    """
    try:
        current_user_id = int(get_jwt_identity())

        # Users can only delete their own account (unless admin)
        current_user = User.query.get(current_user_id)
        if not current_user:
            return error_response('User not found', 404)

        if current_user_id != user_id and current_user.role != 'admin':
            return error_response('Unauthorized to delete this account', 403)

        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        # Require password confirmation when deleting the current account.
        if current_user_id == user_id and current_user.role != 'admin':
            data = request.get_json(silent=True) or {}
            password = data.get('password') or ''
            if not password:
                return error_response('Password is required to delete your account', 400)
            if not current_user.check_password(password):
                return error_response('Password is incorrect', 401)

        _delete_user_data(user_id)

        # Delete the user row directly so SQLAlchemy does not walk remaining relationships.
        User.query.filter(User.id == user_id).delete(synchronize_session=False)
        db.session.commit()

        return success_response(None, 'Account deleted successfully', 200)

    except Exception as e:
        db.session.rollback()
        import traceback
        print('\n===== ERROR in DELETE /api/users/<id> =====')
        print(f'User ID: {user_id}')
        print(f'Exception: {str(e)}')
        print(f'Full traceback:\n{traceback.format_exc()}')
        print('========================================\n')
        return error_response('Failed to delete account', 500, str(e))


@users_bp.route('/role-requests', methods=['POST'])
@jwt_required()
def submit_role_change_request():
    """
    Submit a role change request (client -> coach/both).
    POST /api/users/role-requests
    Body: {requested_role: 'coach' | 'both', reason?: string}
    """
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return error_response('User not found', 404)

        # Only clients can submit role change requests via this flow
        if user.role != 'client':
            return error_response(
                'Only clients can submit a role change request',
                403
            )

        data = request.get_json() or {}
        requested_role = data.get('requested_role')

        if requested_role not in ('coach', 'both'):
            return error_response(
                "Invalid requested role. Must be 'coach' or 'both'",
                400
            )

        # Block duplicates: only one pending request per user at a time
        existing_pending = RoleChangeRequest.query.filter_by(
            user_id=current_user_id,
            status='pending'
        ).first()
        if existing_pending:
            return error_response(
                'You already have a pending role change request',
                409
            )

        req = RoleChangeRequest(
            user_id=current_user_id,
            current_role=user.role,
            requested_role=requested_role,
            reason=(data.get('reason') or '').strip() or None,
            status='pending'
        )
        db.session.add(req)
        db.session.commit()

        return success_response(
            req.to_dict(),
            'Role change request submitted successfully',
            201
        )

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to submit role change request', 500, str(e))


@users_bp.route('/role-requests/me', methods=['GET'])
@jwt_required()
def get_my_role_change_request():
    """
    Get the current user's most recent role change request (if any).
    GET /api/users/role-requests/me
    """
    try:
        current_user_id = int(get_jwt_identity())
        req = (
            RoleChangeRequest.query
            .filter_by(user_id=current_user_id)
            .order_by(RoleChangeRequest.created_at.desc())
            .first()
        )
        if not req:
            return success_response(None, 'No role change request found', 200)

        return success_response(req.to_dict(), 'Role change request retrieved', 200)

    except Exception as e:
        return error_response('Failed to retrieve role change request', 500, str(e))
