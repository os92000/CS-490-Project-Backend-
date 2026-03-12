from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProfile
from utils.validators import is_valid_role
from utils.helpers import success_response, error_response
from middleware.auth_middleware import require_role

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

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
        current_user_id = get_jwt_identity()

        # Users can only delete their own account (unless admin)
        current_user = User.query.get(current_user_id)
        if current_user_id != user_id and current_user.role != 'admin':
            return error_response('Unauthorized to delete this account', 403)

        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)

        # Delete user (cascade will delete all related data)
        db.session.delete(user)
        db.session.commit()

        return success_response(None, 'Account deleted successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete account', 500, str(e))
