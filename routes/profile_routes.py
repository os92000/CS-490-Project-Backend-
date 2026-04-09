from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProfile, Notification
from utils.helpers import success_response, error_response, save_uploaded_file
import os

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')


@profile_bp.route('', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = int(get_jwt_identity())

    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        return success_response(user.to_dict(include_profile=True), 'Profile retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve profile', 500, str(e))

@profile_bp.route('', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    try:
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        if 'first_name' in data: profile.first_name = data['first_name']
        if 'last_name' in data: profile.last_name = data['last_name']
        if 'bio' in data: profile.bio = data['bio']
        if 'phone' in data: profile.phone = data['phone']
        if 'profile_picture' in data: profile.profile_picture = data['profile_picture']

        db.session.commit()
        return success_response(profile.to_dict(), 'Profile updated', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update profile', 500, str(e))

@profile_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    user_id = int(get_jwt_identity())
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return success_response({'notifications': [n.to_dict() for n in notifications]}, 'Notifications retrieved', 200)

@profile_bp.route('/notifications/<int:notif_id>/read', methods=['PATCH'])
@jwt_required()
def mark_notification_read(notif_id):
    """Mark notification as read"""
    user_id = int(get_jwt_identity())

    try:
        notif = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
        if not notif:
            return error_response('Notification not found', 404)

        notif.read = True
        db.session.commit()
        return success_response(notif.to_dict(), 'Notification marked as read', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update notification', 500, str(e))


@profile_bp.route('/picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """Upload a profile picture"""
    user_id = int(get_jwt_identity())

    try:
        if 'file' not in request.files:
            return error_response('file is required', 400)

        file = request.files['file']
        if not file or not file.filename:
            return error_response('No file selected', 400)

        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        upload_folder = os.path.join('uploads', 'profiles')
        filename = save_uploaded_file(file, upload_folder, resize=(400, 400))
        profile.profile_picture = f'/{upload_folder}/{filename}'
        db.session.commit()
        return success_response(profile.to_dict(), 'Profile picture uploaded', 200)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to upload profile picture', 500, str(e))
