from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, User, UserProfile
from utils.validators import is_valid_email, is_valid_password, is_valid_role
from utils.helpers import success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    User registration endpoint (UC 1.1)
    POST /api/auth/signup
    Body: {email, password}
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            return error_response('Email and password are required', 400)

        email = data['email'].strip().lower()
        password = data['password']

        # Validate email format
        if not is_valid_email(email):
            return error_response('Invalid email format', 400)

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return error_response('Email already registered', 409)

        # Validate password strength
        is_valid, message = is_valid_password(password)
        if not is_valid:
            return error_response(message, 400)

        # Create new user
        user = User(email=email)
        user.set_password(password)

        # Create empty profile
        profile = UserProfile(user=user)

        db.session.add(user)
        db.session.add(profile)
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return success_response({
            'user': user.to_dict(include_profile=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 'User registered successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Registration failed', 500, str(e))


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint (UC 1.2)
    POST /api/auth/login
    Body: {email, password}
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            return error_response('Email and password are required', 400)

        email = data['email'].strip().lower()
        password = data['password']

        # Find user
        user = User.query.filter_by(email=email).first()

        # Verify credentials
        if not user or not user.check_password(password):
            return error_response('Invalid email or password', 401)

        # Check if account is disabled
        if user.status != 'active':
            return error_response('Account is disabled', 403)

        # Generate tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return success_response({
            'user': user.to_dict(include_profile=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 'Login successful', 200)

    except Exception as e:
        return error_response('Login failed', 500, str(e))


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint (UC 1.3)
    POST /api/auth/logout
    Note: In JWT, actual logout is handled client-side by removing the token
    This endpoint exists for compatibility and future token blacklisting
    """
    try:
        # In a production app, you would add the token to a blacklist here
        return success_response(None, 'Logout successful', 200)
    except Exception as e:
        return error_response('Logout failed', 500, str(e))


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    POST /api/auth/refresh
    Requires refresh token in Authorization header
    """
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=str(current_user_id))

        return success_response({
            'access_token': new_access_token
        }, 'Token refreshed successfully', 200)

    except Exception as e:
        return error_response('Token refresh failed', 500, str(e))


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user
    GET /api/auth/me
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return error_response('User not found', 404)

        return success_response(user.to_dict(include_profile=True), 'User retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve user', 500, str(e))


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """
    Change user password
    PUT /api/auth/change-password
    Body: {current_password, new_password}
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return error_response('User not found', 404)

        data = request.get_json()

        if not data or 'current_password' not in data or 'new_password' not in data:
            return error_response('Current password and new password are required', 400)

        # Verify current password
        if not user.check_password(data['current_password']):
            return error_response('Current password is incorrect', 401)

        # Validate new password
        is_valid, message = is_valid_password(data['new_password'])
        if not is_valid:
            return error_response(message, 400)

        # Update password
        user.set_password(data['new_password'])
        db.session.commit()

        return success_response(None, 'Password changed successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Password change failed', 500, str(e))
