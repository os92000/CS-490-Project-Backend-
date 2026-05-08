import os
from datetime import datetime

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import CoachRelationship, ProgressPhoto, User, db
from utils.helpers import delete_file, error_response, save_uploaded_file, success_response


progress_photos_bp = Blueprint(
    "progress_photos", __name__, url_prefix="/api/progress-photos"
)


ALLOWED_CATEGORIES = {"front", "back", "side", "other"}


def _parse_optional_date(raw_date):
    if raw_date in (None, ""):
        return None, None
    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date(), None
    except (TypeError, ValueError):
        return None, "date must be in YYYY-MM-DD format"


def _file_extension_allowed(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = current_app.config.get(
        "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"}
    )
    return ext in allowed


@progress_photos_bp.route("", methods=["GET"])
@jwt_required()
def get_my_progress_photos():
    """Get progress photos for the authenticated user."""
    try:
        user_id = int(get_jwt_identity())
        category = (request.args.get("category") or "").strip().lower()

        query = ProgressPhoto.query.filter_by(user_id=user_id)
        if category:
            if category not in ALLOWED_CATEGORIES:
                return error_response("Invalid category", 400)
            query = query.filter(ProgressPhoto.category == category)

        photos = (
            query.order_by(ProgressPhoto.date.desc(), ProgressPhoto.uploaded_at.desc())
            .all()
        )
        return success_response(
            {"photos": [photo.to_dict() for photo in photos]},
            "Progress photos retrieved",
            200,
        )
    except Exception as e:
        return error_response("Failed to retrieve progress photos", 500, str(e))


@progress_photos_bp.route("", methods=["POST"])
@jwt_required()
def upload_progress_photo():
    """Upload a progress photo for the authenticated user."""
    try:
        user_id = int(get_jwt_identity())

        if "photo" not in request.files:
            return error_response("photo is required", 400)

        photo_file = request.files["photo"]
        if not photo_file or not photo_file.filename:
            return error_response("No file selected", 400)

        if not _file_extension_allowed(photo_file.filename):
            allowed = ", ".join(sorted(current_app.config.get("ALLOWED_EXTENSIONS", [])))
            return error_response(f"Unsupported file type. Allowed: {allowed}", 400)

        category = (request.form.get("category") or "other").strip().lower()
        if category not in ALLOWED_CATEGORIES:
            return error_response("Invalid category", 400)

        notes = (request.form.get("notes") or "").strip() or None
        date_value, date_error = _parse_optional_date(request.form.get("date"))
        if date_error:
            return error_response(date_error, 400)

        upload_folder = os.path.join("uploads", "progress_photos")
        filename = save_uploaded_file(photo_file, upload_folder)
        photo_url = f"/{upload_folder.replace(os.sep, '/')}/{filename}"

        photo = ProgressPhoto(
            user_id=user_id,
            photo_url=photo_url,
            category=category,
            notes=notes,
            date=date_value,
        )
        db.session.add(photo)
        db.session.commit()

        return success_response(photo.to_dict(), "Progress photo uploaded", 201)
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to upload progress photo", 500, str(e))


@progress_photos_bp.route("/<int:photo_id>", methods=["DELETE"])
@jwt_required()
def delete_progress_photo(photo_id):
    """Delete a progress photo owned by the authenticated user."""
    try:
        user_id = int(get_jwt_identity())

        photo = ProgressPhoto.query.filter_by(id=photo_id, user_id=user_id).first()
        if not photo:
            return error_response("Progress photo not found", 404)

        relative_file_path = photo.photo_url.lstrip("/")
        db.session.delete(photo)
        db.session.commit()

        delete_file(relative_file_path)
        return success_response(None, "Progress photo deleted", 200)
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to delete progress photo", 500, str(e))


@progress_photos_bp.route("/client/<int:client_id>", methods=["GET"])
@jwt_required()
def get_client_progress_photos(client_id):
    """Get progress photos for a coach's active client."""
    try:
        coach_id = int(get_jwt_identity())

        coach = User.query.get(coach_id)
        if not coach or coach.role not in ("coach", "both"):
            return error_response("Only coaches can view client photos", 403)

        relationship = CoachRelationship.query.filter_by(
            coach_id=coach_id, client_id=client_id, status="active"
        ).first()
        if not relationship:
            return error_response("No active relationship with this client", 403)

        category = (request.args.get("category") or "").strip().lower()
        query = ProgressPhoto.query.filter_by(user_id=client_id)
        if category:
            if category not in ALLOWED_CATEGORIES:
                return error_response("Invalid category", 400)
            query = query.filter(ProgressPhoto.category == category)

        photos = (
            query.order_by(ProgressPhoto.date.desc(), ProgressPhoto.uploaded_at.desc())
            .all()
        )

        return success_response(
            {"photos": [photo.to_dict() for photo in photos]},
            "Client progress photos retrieved",
            200,
        )
    except Exception as e:
        return error_response("Failed to retrieve client progress photos", 500, str(e))
