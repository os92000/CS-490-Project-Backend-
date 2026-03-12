from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CoachRelationship, WorkoutPlan, Review
from utils.helpers import success_response, error_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

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
            'users': [u.to_dict(include_profile=True) for u in users]
        }, 'Users retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve users', 500, str(e))

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
