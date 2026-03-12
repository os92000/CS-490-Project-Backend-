from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import User

def jwt_required_custom():
    """
    Custom JWT required decorator with better error handling
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': 'Authentication required',
                    'error': str(e)
                }), 401
        return decorator
    return wrapper

def get_current_user():
    """Get the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user
    except Exception:
        return None

def require_role(*allowed_roles):
    """
    Decorator to require specific user roles
    Usage: @require_role('admin', 'coach')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)

                if not user:
                    return jsonify({
                        'success': False,
                        'data': None,
                        'message': 'User not found',
                        'error': None
                    }), 404

                if user.status != 'active':
                    return jsonify({
                        'success': False,
                        'data': None,
                        'message': 'Account is disabled',
                        'error': None
                    }), 403

                # Allow if user has any of the allowed roles
                # 'both' role has access to both client and coach endpoints
                user_roles = [user.role]
                if user.role == 'both':
                    user_roles.extend(['client', 'coach'])

                if not any(role in allowed_roles for role in user_roles):
                    return jsonify({
                        'success': False,
                        'data': None,
                        'message': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                        'error': None
                    }), 403

                return fn(*args, **kwargs)

            except Exception as e:
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': 'Authorization failed',
                    'error': str(e)
                }), 401

        return wrapper
    return decorator

def optional_jwt():
    """
    Decorator for optional JWT authentication
    Allows both authenticated and unauthenticated access
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                pass
            return fn(*args, **kwargs)
        return wrapper
    return decorator
