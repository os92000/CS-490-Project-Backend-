from flask import Blueprint, request, Response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from itsdangerous import URLSafeSerializer, BadSignature
import json
import hashlib
from models import (
    db,
    User,
    Exercise,
    WorkoutPlan,
    WorkoutDay,
    PlanExercise,
    WorkoutLog,
    ExerciseLog,
    CoachRelationship,
    WorkoutPlanMetadata,
    WorkoutTemplate,
    WorkoutPlanAssignment,
    CalendarNote,
)
from utils.helpers import success_response, error_response
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_

workouts_bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")


# ============================================
# Calendar Feed Token Helpers
# ============================================


def _feed_serializer():
    """Signed serializer used for subscription feed tokens (stateless)."""
    secret = current_app.config.get("SECRET_KEY", "dev-secret")
    return URLSafeSerializer(secret, salt="workout-calendar-feed")


def _make_feed_token(user_id):
    return _feed_serializer().dumps({"uid": int(user_id)})


def _parse_feed_token(token):
    try:
        data = _feed_serializer().loads(token)
        return int(data.get("uid"))
    except (BadSignature, TypeError, ValueError):
        return None


def _ics_escape(value):
    """Escape a value for inclusion in an iCal text field (RFC 5545)."""
    if value is None:
        return ""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _ics_fold(line):
    """Fold long iCal lines at 75 octets per RFC 5545."""
    if len(line) <= 75:
        return line
    chunks = [line[:75]]
    rest = line[75:]
    while rest:
        chunks.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(chunks)


def _build_workout_ics(user_id, host_url):
    """Build an iCalendar (.ics) document covering scheduled days + assignments + logs for a user."""
    today = date.today()
    window_start = today - timedelta(days=180)
    window_end = today + timedelta(days=365)

    # Auto-distributed scheduled days from plans with date ranges
    plans = WorkoutPlan.query.filter_by(client_id=user_id, status="active").all()
    scheduled_days = []

    for plan in plans:
        if not plan.start_date or not plan.end_date:
            continue
        days = (
            WorkoutDay.query.filter_by(plan_id=plan.id)
            .order_by(WorkoutDay.day_number)
            .all()
        )
        if not days:
            continue
        total_days = len(days)
        span = (plan.end_date - plan.start_date).days
        for i, day in enumerate(days):
            if total_days == 1:
                scheduled_date = plan.start_date
            else:
                scheduled_date = plan.start_date + timedelta(
                    days=round(span * i / (total_days - 1))
                )
            if scheduled_date < window_start or scheduled_date > window_end:
                continue
            exercises = PlanExercise.query.filter_by(workout_day_id=day.id).all()
            scheduled_days.append(
                {
                    "plan_name": plan.name,
                    "plan_description": plan.description,
                    "day_name": day.name,
                    "day_notes": day.notes,
                    "scheduled_date": scheduled_date,
                    "exercises": exercises,
                }
            )

    assignments = WorkoutPlanAssignment.query.filter(
        WorkoutPlanAssignment.user_id == user_id,
        WorkoutPlanAssignment.assigned_date >= window_start,
        WorkoutPlanAssignment.assigned_date <= window_end,
    ).all()

    logs = WorkoutLog.query.filter(
        WorkoutLog.client_id == user_id,
        WorkoutLog.date >= window_start,
        WorkoutLog.date <= window_end,
    ).all()

    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//FitApp//Workout Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:FitApp Workouts",
        "X-WR-CALDESC:Your FitApp workout schedule and completed sessions",
        "X-WR-TIMEZONE:UTC",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]

    for sd in scheduled_days:
        dt = sd["scheduled_date"]
        dt_next = dt + timedelta(days=1)
        plan_name = sd["plan_name"]
        day_name = sd["day_name"]
        summary = f"💪 {plan_name}"
        if day_name:
            summary = f"💪 {plan_name} — {day_name}"

        desc_parts = []
        if sd["plan_description"]:
            desc_parts.append(sd["plan_description"])
        if day_name:
            desc_parts.append(f"Day: {day_name}")
        if sd["day_notes"]:
            desc_parts.append(sd["day_notes"])
        if sd["exercises"]:
            ex_list = []
            for ex in sd["exercises"]:
                ex_name = ex.exercise.name if ex.exercise else "Unknown"
                ex_detail = ex_name
                if ex.sets:
                    ex_detail += f" — {ex.sets} sets"
                if ex.reps:
                    ex_detail += f" x {ex.reps}"
                ex_list.append(ex_detail)
            desc_parts.append("Exercises:\n" + "\n".join(ex_list))
        desc_parts.append(f"View in FitApp: {host_url.rstrip('/')}/my-workouts")
        description = "\n".join(desc_parts)

        uid = f"scheduled-{hashlib.md5(f'{plan_name}-{day_name}-{dt}'.encode()).hexdigest()[:12]}@fitapp"

        lines.extend(
            [
                "BEGIN:VEVENT",
                _ics_fold(f"UID:{uid}"),
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{dt_next.strftime('%Y%m%d')}",
                _ics_fold(f"SUMMARY:{_ics_escape(summary)}"),
                _ics_fold(f"DESCRIPTION:{_ics_escape(description)}"),
                "CATEGORIES:Workout,Fitness",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                _ics_fold(
                    f"DESCRIPTION:{_ics_escape('Workout reminder: ' + plan_name)}"
                ),
                "TRIGGER:-PT30M",
                "END:VALARM",
                "END:VEVENT",
            ]
        )

    for a in assignments:
        dt = a.assigned_date
        dt_next = dt + timedelta(days=1)
        plan_name = a.plan.name if a.plan else "Workout"
        day_name = a.workout_day.name if a.workout_day else None
        summary = f"💪 {plan_name}"
        if day_name:
            summary = f"💪 {plan_name} — {day_name}"

        desc_parts = []
        if a.plan and a.plan.description:
            desc_parts.append(a.plan.description)
        if day_name:
            desc_parts.append(f"Day: {day_name}")
        if a.workout_day and a.workout_day.notes:
            desc_parts.append(a.workout_day.notes)
        desc_parts.append(f"View in FitApp: {host_url.rstrip('/')}/my-workouts")
        description = "\n".join(desc_parts)

        uid = f"assignment-{a.id}-{hashlib.md5(str(a.id).encode()).hexdigest()[:8]}@fitapp"

        lines.extend(
            [
                "BEGIN:VEVENT",
                _ics_fold(f"UID:{uid}"),
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{dt_next.strftime('%Y%m%d')}",
                _ics_fold(f"SUMMARY:{_ics_escape(summary)}"),
                _ics_fold(f"DESCRIPTION:{_ics_escape(description)}"),
                "CATEGORIES:Workout,Fitness",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                _ics_fold(
                    f"DESCRIPTION:{_ics_escape('Workout reminder: ' + plan_name)}"
                ),
                "TRIGGER:-PT30M",
                "END:VALARM",
                "END:VEVENT",
            ]
        )

    for log in logs:
        dt = log.date
        dt_next = dt + timedelta(days=1)
        title = log.workout_name or (log.plan.name if log.plan else "Workout session")
        summary = f"✅ {title}"

        desc_parts = []
        if log.duration_minutes:
            desc_parts.append(f"Duration: {log.duration_minutes} min")
        if log.rating:
            desc_parts.append(f"Rating: {'★' * log.rating}{'☆' * (5 - log.rating)}")
        if log.calories_burned:
            desc_parts.append(f"Calories burned: {log.calories_burned}")
        if log.muscle_group:
            desc_parts.append(f"Muscle group: {log.muscle_group}")
        if log.notes:
            desc_parts.append(log.notes)
        description = "\n".join(desc_parts) if desc_parts else "Completed workout"

        uid = f"log-{log.id}-{hashlib.md5(str(log.id).encode()).hexdigest()[:8]}@fitapp"

        lines.extend(
            [
                "BEGIN:VEVENT",
                _ics_fold(f"UID:{uid}"),
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{dt_next.strftime('%Y%m%d')}",
                _ics_fold(f"SUMMARY:{_ics_escape(summary)}"),
                _ics_fold(f"DESCRIPTION:{_ics_escape(description)}"),
                "CATEGORIES:Workout,Completed",
                "STATUS:CONFIRMED",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# ============================================
# Exercise Management
# ============================================


@workouts_bp.route("/public/exercises", methods=["GET"])
def get_public_exercises():
    """
    Public exercise bank for discovery pages (no login required).
    GET /api/workouts/public/exercises?page=1&per_page=12&category=strength&search=bench
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 12, type=int)
        page = max(1, page)
        per_page = max(1, min(per_page, 48))

        query = Exercise.query.filter(Exercise.is_public == True)

        category = request.args.get("category")
        if category:
            query = query.filter_by(category=category)

        muscle_group = request.args.get("muscle_group")
        if muscle_group:
            query = query.filter_by(muscle_group=muscle_group)

        difficulty = request.args.get("difficulty")
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        search = request.args.get("search")
        if search:
            query = query.filter(Exercise.name.ilike(f"%{search}%"))

        paginated = query.order_by(Exercise.name.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return success_response(
            {
                "exercises": [ex.to_dict() for ex in paginated.items],
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": paginated.page,
                "per_page": per_page,
                "has_next": paginated.has_next,
                "has_prev": paginated.has_prev,
            },
            "Public exercises retrieved successfully",
            200,
        )

    except Exception as e:
        return error_response("Failed to retrieve public exercises", 500, str(e))


@workouts_bp.route("/exercises", methods=["GET"])
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
        category = request.args.get("category")
        if category:
            query = query.filter_by(category=category)

        # Filter by muscle group
        muscle_group = request.args.get("muscle_group")
        if muscle_group:
            query = query.filter_by(muscle_group=muscle_group)

        # Filter by difficulty
        difficulty = request.args.get("difficulty")
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

        # Search by name
        search = request.args.get("search")
        if search:
            query = query.filter(Exercise.name.ilike(f"%{search}%"))

        # Only show public exercises or user's own exercises
        query = query.filter(
            or_(Exercise.is_public == True, Exercise.created_by == user_id)
        )

        exercises = query.all()

        return success_response(
            {"exercises": [ex.to_dict() for ex in exercises]},
            "Exercises retrieved successfully",
            200,
        )

    except Exception as e:
        import traceback

        print(f"\n===== ERROR in GET /exercises =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to retrieve exercises", 500, str(e))


@workouts_bp.route("/library", methods=["GET"])
@jwt_required()
def get_workout_library():
    """
    Get all placeholder workouts from the workout library.
    GET /api/workouts/library
    Optional filters: ?category=cardio&muscle_group=legs
    """
    try:
        query = Exercise.query.filter_by(is_library_workout=True, is_public=True)

        category = request.args.get("category")
        if category:
            query = query.filter_by(category=category)

        muscle_group = request.args.get("muscle_group")
        if muscle_group:
            query = query.filter_by(muscle_group=muscle_group)

        workouts = query.order_by(Exercise.category, Exercise.name).all()

        return success_response(
            {"workouts": [w.to_dict() for w in workouts]},
            "Workout library retrieved successfully",
            200,
        )

    except Exception as e:
        import traceback

        print(f"\n===== ERROR in GET /library =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to retrieve workout library", 500, str(e))


@workouts_bp.route("/exercises", methods=["POST"])
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

        if not data or "name" not in data:
            return error_response("Exercise name is required", 400)

        exercise = Exercise(
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            muscle_group=data.get("muscle_group"),
            equipment=data.get("equipment"),
            difficulty=data.get("difficulty"),
            video_url=data.get("video_url"),
            instructions=data.get("instructions"),
            created_by=user_id,
            is_public=data.get("is_public", False),
        )

        db.session.add(exercise)
        db.session.commit()

        return success_response(
            exercise.to_dict(), "Exercise created successfully", 201
        )

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to create exercise", 500, str(e))


@workouts_bp.route("/templates", methods=["GET", "POST"])
@jwt_required()
def workout_templates():
    """
    Browse or create workout templates
    GET /api/workouts/templates
    POST /api/workouts/templates
    """
    try:
        user_id = int(get_jwt_identity())

        if request.method == "GET":
            query = WorkoutTemplate.query.filter(
                or_(
                    and_(
                        WorkoutTemplate.is_public == True,
                        WorkoutTemplate.approved == True,
                    ),
                    WorkoutTemplate.created_by == user_id,
                )
            )

            goal = request.args.get("goal")
            difficulty = request.args.get("difficulty")
            plan_type = request.args.get("plan_type")
            if goal:
                query = query.filter(WorkoutTemplate.goal.ilike(f"%{goal}%"))
            if difficulty:
                query = query.filter_by(difficulty=difficulty)
            if plan_type:
                query = query.filter_by(plan_type=plan_type)

            templates = query.order_by(WorkoutTemplate.created_at.desc()).all()
            return success_response(
                {"templates": [template.to_dict() for template in templates]},
                "Workout templates retrieved successfully",
                200,
            )

        data = request.get_json() or {}
        if not data.get("name") or not data.get("template_data"):
            return error_response("name and template_data are required", 400)

        template = WorkoutTemplate(
            name=data["name"],
            description=data.get("description"),
            goal=data.get("goal"),
            difficulty=data.get("difficulty"),
            plan_type=data.get("plan_type"),
            duration_weeks=data.get("duration_weeks"),
            template_data=json.dumps(data["template_data"]),
            created_by=user_id,
            is_public=data.get("is_public", False),
            approved=False,
        )
        db.session.add(template)
        db.session.commit()
        return success_response(
            template.to_dict(), "Workout template created successfully", 201
        )
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to manage workout templates", 500, str(e))


@workouts_bp.route("/templates/<int:template_id>/customize", methods=["POST"])
@jwt_required()
def customize_workout_template(template_id):
    """
    Customize a template into a self-directed workout plan
    POST /api/workouts/templates/{template_id}/customize
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        template = WorkoutTemplate.query.get(template_id)
        if not template:
            return error_response("Workout template not found", 404)

        if not template.approved and template.created_by != user_id:
            return error_response("Template is not available", 403)

        template_data = template.to_dict()["template_data"]
        days = data.get("days", template_data.get("days", []))

        plan = WorkoutPlan(
            name=data.get("name", f"{template.name} (Customized)"),
            description=data.get("description", template.description),
            coach_id=user_id,
            client_id=user_id,
            start_date=datetime.fromisoformat(data["start_date"]).date()
            if data.get("start_date")
            else None,
            end_date=datetime.fromisoformat(data["end_date"]).date()
            if data.get("end_date")
            else None,
        )
        db.session.add(plan)
        db.session.flush()

        db.session.add(
            WorkoutPlanMetadata(
                plan_id=plan.id,
                goal=data.get("goal", template.goal),
                difficulty=data.get("difficulty", template.difficulty),
                plan_type=data.get("plan_type", template.plan_type),
                duration_weeks=data.get("duration_weeks", template.duration_weeks),
            )
        )

        for day_data in days:
            day = WorkoutDay(
                plan_id=plan.id,
                name=day_data.get("name"),
                day_number=day_data.get("day_number"),
                notes=day_data.get("notes"),
            )
            db.session.add(day)
            db.session.flush()

            for exercise_data in day_data.get("exercises", []):
                db.session.add(
                    PlanExercise(
                        workout_day_id=day.id,
                        exercise_id=exercise_data["exercise_id"],
                        order=exercise_data.get("order"),
                        sets=exercise_data.get("sets"),
                        reps=exercise_data.get("reps"),
                        duration_minutes=exercise_data.get("duration_minutes"),
                        rest_seconds=exercise_data.get("rest_seconds"),
                        weight=exercise_data.get("weight"),
                        notes=exercise_data.get("notes"),
                    )
                )

        db.session.commit()
        return success_response(
            plan.to_dict(include_days=True),
            "Workout template customized successfully",
            201,
        )
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to customize workout template", 500, str(e))


# ============================================
# Workout Plan Management
# ============================================


@workouts_bp.route("/plans", methods=["GET"])
@jwt_required()
def get_workout_plans():
    """
    Get workout plans for the current user (as client or coach)
    GET /api/workouts/plans?role=coach (returns plans created by coach)
    GET /api/workouts/plans?role=client (returns plans assigned to client)
    """
    try:
        user_id = int(get_jwt_identity())
        role = request.args.get("role", "client")

        if role == "coach":
            plans = WorkoutPlan.query.filter_by(coach_id=user_id).all()
        else:
            plans = WorkoutPlan.query.filter_by(client_id=user_id).all()

        metadata_by_plan_id = {}
        if plans:
            metadata_rows = WorkoutPlanMetadata.query.filter(
                WorkoutPlanMetadata.plan_id.in_([plan.id for plan in plans])
            ).all()
            metadata_by_plan_id = {row.plan_id: row for row in metadata_rows}

        goal = request.args.get("goal")
        difficulty = request.args.get("difficulty")
        plan_type = request.args.get("plan_type")
        duration_weeks = request.args.get("duration_weeks", type=int)

        if any([goal, difficulty, plan_type, duration_weeks]):
            filtered_plans = []
            for plan in plans:
                metadata = metadata_by_plan_id.get(plan.id)
                if goal and (
                    not metadata or goal.lower() not in (metadata.goal or "").lower()
                ):
                    continue
                if difficulty and (not metadata or metadata.difficulty != difficulty):
                    continue
                if plan_type and (not metadata or metadata.plan_type != plan_type):
                    continue
                if duration_weeks and (
                    not metadata or metadata.duration_weeks != duration_weeks
                ):
                    continue
                filtered_plans.append(plan)
            plans = filtered_plans

        # Safely serialize plans with error handling
        plans_data = []
        for plan in plans:
            try:
                payload = plan.to_dict()
                metadata = metadata_by_plan_id.get(plan.id)
                if metadata:
                    payload.update(metadata.to_dict())
                if plan.client:
                    payload["client"] = {
                        "id": plan.client.id,
                        "email": plan.client.email,
                        "profile": plan.client.profile.to_dict()
                        if plan.client.profile
                        else None,
                    }
                plans_data.append(payload)
            except Exception as plan_error:
                print(f"Error serializing plan {plan.id}: {str(plan_error)}")
                continue

        return success_response(
            {"plans": plans_data}, "Workout plans retrieved successfully", 200
        )

    except Exception as e:
        print(f"Error retrieving workout plans: {str(e)}")
        return error_response("Failed to retrieve workout plans", 500, str(e))


@workouts_bp.route("/plans/<int:plan_id>/clients", methods=["GET"])
@jwt_required()
def get_plan_clients(plan_id):
    """
    Get the client(s) assigned to a workout plan (for coaches)
    GET /api/workouts/plans/{plan_id}/clients
    """
    try:
        user_id = int(get_jwt_identity())

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response("Workout plan not found", 404)

        if plan.coach_id != user_id:
            return error_response("Unauthorized to access this plan", 403)

        client_data = plan.client.to_dict(include_profile=True)
        client_data["plan_status"] = plan.status
        client_data["start_date"] = (
            plan.start_date.isoformat() if plan.start_date else None
        )
        client_data["end_date"] = plan.end_date.isoformat() if plan.end_date else None

        return success_response(
            {"plan": plan.to_dict(), "clients": [client_data]},
            "Plan clients retrieved successfully",
            200,
        )

    except Exception as e:
        return error_response("Failed to retrieve plan clients", 500, str(e))


@workouts_bp.route("/plans/<int:plan_id>", methods=["GET"])
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
            return error_response("Workout plan not found", 404)

        # Verify user has access
        if plan.coach_id != user_id and plan.client_id != user_id:
            return error_response("Unauthorized to access this workout plan", 403)

        return success_response(
            plan.to_dict(include_days=True), "Workout plan retrieved successfully", 200
        )

    except Exception as e:
        return error_response("Failed to retrieve workout plan", 500, str(e))


@workouts_bp.route("/plans", methods=["POST"])
@jwt_required()
def create_workout_plan():
    """
    Create a workout plan.
    POST /api/workouts/plans
    Body: {name, description, client_id?, start_date, end_date, days: [...]}

    - If client_id is omitted (or equals the current user), a self-plan is created
      (coach_id = NULL, client_id = current_user).
    - If client_id is another user, the current user must have an active coach
      relationship with them, and coach_id is set to the current user.
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or "name" not in data:
            return error_response("name is required", 400)

        raw_client_id = data.get("client_id")
        # Empty string or missing => self-plan
        if raw_client_id in (None, "", 0):
            client_id = user_id
            coach_id = None
        else:
            try:
                client_id = int(raw_client_id)
            except (ValueError, TypeError):
                return error_response("Invalid client_id", 400)

            if client_id == user_id:
                # User explicitly set themselves as client — treat as self-plan
                coach_id = None
            else:
                # Creating for another user — must be an active coach
                relationship = CoachRelationship.query.filter_by(
                    coach_id=user_id, client_id=client_id, status="active"
                ).first()
                if not relationship:
                    return error_response(
                        "No active relationship with this client", 403
                    )
                coach_id = user_id

        # Create plan
        plan = WorkoutPlan(
            name=data["name"],
            description=data.get("description"),
            coach_id=coach_id,
            client_id=client_id,
            start_date=datetime.fromisoformat(data["start_date"]).date()
            if data.get("start_date")
            else None,
            end_date=datetime.fromisoformat(data["end_date"]).date()
            if data.get("end_date")
            else None,
        )

        db.session.add(plan)
        db.session.flush()  # Get plan.id before adding days

        # Add workout days if provided
        if "days" in data and isinstance(data["days"], list):
            for day_data in data["days"]:
                day = WorkoutDay(
                    plan_id=plan.id,
                    name=day_data["name"],
                    day_number=day_data.get("day_number"),
                    notes=day_data.get("notes"),
                )
                db.session.add(day)
                db.session.flush()  # Get day.id before adding exercises

                # Add exercises to the day if provided
                if "exercises" in day_data and isinstance(day_data["exercises"], list):
                    for ex_data in day_data["exercises"]:
                        plan_exercise = PlanExercise(
                            workout_day_id=day.id,
                            exercise_id=ex_data["exercise_id"],
                            order=ex_data.get("order"),
                            sets=ex_data.get("sets"),
                            reps=ex_data.get("reps"),
                            duration_minutes=ex_data.get("duration_minutes"),
                            rest_seconds=ex_data.get("rest_seconds"),
                            weight=ex_data.get("weight"),
                            notes=ex_data.get("notes"),
                        )
                        db.session.add(plan_exercise)

        db.session.commit()

        return success_response(
            plan.to_dict(include_days=True), "Workout plan created successfully", 201
        )

    except Exception as e:
        db.session.rollback()
        import traceback

        print(f"\n===== ERROR in POST /plans =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to create workout plan", 500, str(e))


def _user_can_modify_plan(plan, user_id):
    """
    The plan owner can modify it.
    Owner = coach_id if set (coach-created plan), otherwise client_id (self-created).
    """
    if plan.coach_id is not None:
        return plan.coach_id == user_id
    return plan.client_id == user_id


@workouts_bp.route("/plans/<int:plan_id>", methods=["PUT"])
@jwt_required()
def update_workout_plan(plan_id):
    """
    Update a workout plan. Only the owner (coach if coach-created, else the
    client who created it) can modify.
    PUT /api/workouts/plans/{plan_id}
    Body: {name, description, start_date, end_date, status}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response("Workout plan not found", 404)

        if not _user_can_modify_plan(plan, user_id):
            return error_response("Only the plan owner can update this plan", 403)

        # Update fields
        if "name" in data:
            plan.name = data["name"]
        if "description" in data:
            plan.description = data["description"]
        if "start_date" in data:
            plan.start_date = (
                datetime.fromisoformat(data["start_date"]).date()
                if data["start_date"]
                else None
            )
        if "end_date" in data:
            plan.end_date = (
                datetime.fromisoformat(data["end_date"]).date()
                if data["end_date"]
                else None
            )
        if "status" in data:
            plan.status = data["status"]

        db.session.commit()

        return success_response(
            plan.to_dict(include_days=True), "Workout plan updated successfully", 200
        )

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to update workout plan", 500, str(e))


@workouts_bp.route("/plans/<int:plan_id>", methods=["DELETE"])
@jwt_required()
def delete_workout_plan(plan_id):
    """
    Delete a workout plan. Only the owner can delete.
    DELETE /api/workouts/plans/{plan_id}
    """
    try:
        user_id = int(get_jwt_identity())

        plan = WorkoutPlan.query.get(plan_id)
        if not plan:
            return error_response("Workout plan not found", 404)

        if not _user_can_modify_plan(plan, user_id):
            return error_response("Only the plan owner can delete this plan", 403)

        db.session.delete(plan)
        db.session.commit()

        return success_response(None, "Workout plan deleted successfully", 200)

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to delete workout plan", 500, str(e))


@workouts_bp.route("/assignments", methods=["POST", "DELETE"])
@jwt_required()
def workout_assignments():
    """Assign workout plans to specific calendar days"""
    user_id = int(get_jwt_identity())

    if request.method == "POST":
        try:
            data = request.get_json() or {}
            if not data.get("plan_id") or not data.get("assigned_date"):
                return error_response("plan_id and assigned_date are required", 400)

            plan = WorkoutPlan.query.get(data["plan_id"])
            if not plan or plan.client_id != user_id:
                return error_response("Workout plan not found", 404)

            assignment = WorkoutPlanAssignment(
                user_id=user_id,
                plan_id=plan.id,
                workout_day_id=data.get("workout_day_id"),
                assigned_date=datetime.fromisoformat(data["assigned_date"]).date(),
            )
            db.session.add(assignment)
            db.session.commit()
            return success_response(
                assignment.to_dict(), "Workout assigned to calendar", 201
            )
        except Exception as e:
            db.session.rollback()
            return error_response("Failed to assign workout plan", 500, str(e))

    try:
        assignment_id = request.args.get("assignment_id", type=int)
        assignment = WorkoutPlanAssignment.query.filter_by(
            id=assignment_id, user_id=user_id
        ).first()
        if not assignment:
            return error_response("Assignment not found", 404)
        db.session.delete(assignment)
        db.session.commit()
        return success_response(None, "Workout assignment removed", 200)
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to remove workout assignment", 500, str(e))


# ============================================
# Workout Logging
# ============================================


@workouts_bp.route("/logs", methods=["GET"])
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
        start_date = request.args.get("start_date")
        if start_date:
            query = query.filter(
                WorkoutLog.date >= datetime.fromisoformat(start_date).date()
            )

        end_date = request.args.get("end_date")
        if end_date:
            query = query.filter(
                WorkoutLog.date <= datetime.fromisoformat(end_date).date()
            )

        logs = query.order_by(WorkoutLog.date.desc()).all()

        return success_response(
            {"logs": [log.to_dict() for log in logs]},
            "Workout logs retrieved successfully",
            200,
        )

    except Exception as e:
        import traceback

        print(f"\n===== ERROR in GET /logs =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to retrieve workout logs", 500, str(e))


@workouts_bp.route("/logs", methods=["POST"])
@jwt_required()
def create_workout_log():
    """
    Log a completed workout
    POST /api/workouts/logs
    Body: {
      plan_id, workout_day_id, date, duration_minutes, notes, rating,
      library_exercise_id, workout_name, calories_burned, exercise_type, muscle_group,
      exercises: [...]
    }
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or "date" not in data:
            return error_response("date is required", 400)

        # Convert empty strings to None for foreign keys
        plan_id = data.get("plan_id") or None
        workout_day_id = data.get("workout_day_id") or None
        library_exercise_id = data.get("library_exercise_id") or None

        def _to_int(value):
            if value in (None, ""):
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        duration_minutes = _to_int(data.get("duration_minutes"))
        rating = _to_int(data.get("rating"))
        calories_burned = _to_int(data.get("calories_burned"))
        library_exercise_id = _to_int(library_exercise_id)

        # If a library exercise is referenced, prefer its values when the client
        # didn't supply their own.
        workout_name = data.get("workout_name")
        exercise_type = data.get("exercise_type")
        muscle_group = data.get("muscle_group")
        if library_exercise_id:
            lib_exercise = Exercise.query.get(library_exercise_id)
            if lib_exercise and lib_exercise.is_library_workout:
                if not workout_name:
                    workout_name = lib_exercise.name
                if not exercise_type:
                    exercise_type = lib_exercise.category
                if not muscle_group:
                    muscle_group = lib_exercise.muscle_group
                if calories_burned is None:
                    calories_burned = lib_exercise.calories
                if duration_minutes is None:
                    duration_minutes = lib_exercise.default_duration_minutes

        # Create workout log
        log = WorkoutLog(
            client_id=user_id,
            plan_id=plan_id,
            workout_day_id=workout_day_id,
            library_exercise_id=library_exercise_id,
            workout_name=workout_name or None,
            calories_burned=calories_burned,
            exercise_type=exercise_type or None,
            muscle_group=muscle_group or None,
            date=datetime.fromisoformat(data["date"]).date(),
            duration_minutes=duration_minutes,
            notes=data.get("notes"),
            rating=rating,
            completed=data.get("completed", True),
        )

        db.session.add(log)
        db.session.flush()  # Get log.id

        # Add exercise logs if provided
        if "exercises" in data and isinstance(data["exercises"], list):
            for ex_data in data["exercises"]:
                exercise_log = ExerciseLog(
                    workout_log_id=log.id,
                    exercise_id=ex_data["exercise_id"],
                    sets_completed=ex_data.get("sets_completed"),
                    reps_completed=ex_data.get("reps_completed"),
                    weight_used=ex_data.get("weight_used"),
                    duration_minutes=ex_data.get("duration_minutes"),
                    notes=ex_data.get("notes"),
                )
                db.session.add(exercise_log)

        db.session.commit()

        return success_response(
            log.to_dict(include_exercises=True), "Workout logged successfully", 201
        )

    except Exception as e:
        db.session.rollback()
        import traceback

        print(f"\n===== ERROR in POST /logs =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to log workout", 500, str(e))


@workouts_bp.route("/logs/<int:log_id>", methods=["PUT"])
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
            return error_response("Workout log not found", 404)

        # Only owner can update
        if log.client_id != user_id:
            return error_response("Unauthorized to update this workout log", 403)

        # Update fields
        if "duration_minutes" in data:
            log.duration_minutes = data["duration_minutes"]
        if "notes" in data:
            log.notes = data["notes"]
        if "rating" in data:
            log.rating = data["rating"]
        if "completed" in data:
            log.completed = data["completed"]

        db.session.commit()

        return success_response(
            log.to_dict(include_exercises=True), "Workout log updated successfully", 200
        )

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to update workout log", 500, str(e))


@workouts_bp.route("/logs/<int:log_id>", methods=["DELETE"])
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
            return error_response("Workout log not found", 404)

        # Only owner can delete
        if log.client_id != user_id:
            return error_response("Unauthorized to delete this workout log", 403)

        db.session.delete(log)
        db.session.commit()

        return success_response(None, "Workout log deleted successfully", 200)

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to delete workout log", 500, str(e))


# ============================================
# Calendar & Stats
# ============================================


@workouts_bp.route("/calendar", methods=["GET"])
@jwt_required()
def get_workout_calendar():
    """
    Get workout calendar for a month
    GET /api/workouts/calendar?year=2024&month=1

    Returns:
      - logs: completed workout sessions
      - scheduled_days: auto-distributed workout days from plans with date ranges
      - plans_without_dates: active plans that have no start/end date
      - notes: calendar notes for the month
    """
    try:
        user_id = int(get_jwt_identity())

        year = request.args.get("year", datetime.now().year, type=int)
        month = request.args.get("month", datetime.now().month, type=int)

        from calendar import monthrange

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # Completed workout logs
        logs = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= first_day,
            WorkoutLog.date <= last_day,
        ).all()

        # Active workout plans for this user
        plans = WorkoutPlan.query.filter_by(client_id=user_id, status="active").all()

        # Auto-distribute workout days for plans that have a date range
        scheduled_days = []
        plans_without_dates = []

        for plan in plans:
            if not plan.start_date or not plan.end_date:
                plans_without_dates.append(plan.to_dict())
                continue

            days = (
                WorkoutDay.query.filter_by(plan_id=plan.id)
                .order_by(WorkoutDay.day_number)
                .all()
            )
            if not days:
                continue

            total_days = len(days)
            span = (plan.end_date - plan.start_date).days

            for i, day in enumerate(days):
                if total_days == 1:
                    scheduled_date = plan.start_date
                else:
                    scheduled_date = plan.start_date + timedelta(
                        days=round(span * i / (total_days - 1))
                    )

                if scheduled_date < first_day or scheduled_date > last_day:
                    continue

                exercises = PlanExercise.query.filter_by(workout_day_id=day.id).all()
                scheduled_days.append(
                    {
                        "id": f"scheduled-{plan.id}-{day.id}",
                        "plan_id": plan.id,
                        "plan_name": plan.name,
                        "plan_description": plan.description,
                        "day_id": day.id,
                        "day_name": day.name,
                        "day_number": day.day_number,
                        "day_notes": day.notes,
                        "scheduled_date": scheduled_date.isoformat(),
                        "exercises": [
                            {
                                "name": ex.exercise.name if ex.exercise else "Unknown",
                                "sets": ex.sets,
                                "reps": ex.reps,
                                "weight": ex.weight,
                                "rest_seconds": ex.rest_seconds,
                                "notes": ex.notes,
                            }
                            for ex in exercises
                        ],
                    }
                )

        # Calendar notes for the month
        notes = (
            CalendarNote.query.filter(
                CalendarNote.user_id == user_id,
                CalendarNote.date >= first_day,
                CalendarNote.date <= last_day,
            )
            .order_by(CalendarNote.date)
            .all()
        )

        return success_response(
            {
                "logs": [log.to_dict() for log in logs],
                "scheduled_days": scheduled_days,
                "plans_without_dates": plans_without_dates,
                "notes": [note.to_dict() for note in notes],
            },
            "Calendar data retrieved successfully",
            200,
        )

    except Exception as e:
        return error_response("Failed to retrieve calendar data", 500, str(e))


@workouts_bp.route("/calendar/notes", methods=["POST"])
@jwt_required()
def create_calendar_note():
    """
    Add a note to a calendar date
    POST /api/workouts/calendar/notes
    Body: { "date": "2024-01-15", "note": "Rest day - focus on recovery" }
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data.get("date") or not data.get("note"):
            return error_response("Date and note are required", 400)

        note_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        note = CalendarNote(user_id=user_id, date=note_date, note=data["note"])
        db.session.add(note)
        db.session.commit()

        return success_response(note.to_dict(), "Note added", 201)

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to add note", 500, str(e))


@workouts_bp.route("/calendar/notes", methods=["GET"])
@jwt_required()
def get_calendar_notes():
    """
    Get calendar notes for the current user
    GET /api/workouts/calendar/notes?date=2024-01-15 (optional date filter)
    """
    try:
        user_id = int(get_jwt_identity())
        date_filter = request.args.get("date")

        query = CalendarNote.query.filter_by(user_id=user_id)
        if date_filter:
            note_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter_by(date=note_date)

        notes = query.order_by(CalendarNote.date.desc()).all()
        return success_response(
            {"notes": [n.to_dict() for n in notes]}, "Notes retrieved", 200
        )

    except Exception as e:
        return error_response("Failed to retrieve notes", 500, str(e))


@workouts_bp.route("/calendar/notes/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_calendar_note(note_id):
    """
    Delete a calendar note
    DELETE /api/workouts/calendar/notes/<note_id>
    """
    try:
        user_id = int(get_jwt_identity())
        note = CalendarNote.query.filter_by(id=note_id, user_id=user_id).first()

        if not note:
            return error_response("Note not found", 404)

        db.session.delete(note)
        db.session.commit()
        return success_response(None, "Note deleted", 200)

    except Exception as e:
        db.session.rollback()
        return error_response("Failed to delete note", 500, str(e))


@workouts_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_workout_stats():
    """
    Get workout statistics
    GET /api/workouts/stats?period=30 (last 30 days)
    """
    try:
        user_id = int(get_jwt_identity())
        period = request.args.get("period", 30, type=int)

        # Calculate date range
        end_date = date.today()
        from datetime import timedelta

        start_date = end_date - timedelta(days=period)

        # Get logs for the period
        logs = WorkoutLog.query.filter(
            WorkoutLog.client_id == user_id,
            WorkoutLog.date >= start_date,
            WorkoutLog.date <= end_date,
            WorkoutLog.completed == True,
        ).all()

        # Calculate stats
        total_workouts = len(logs)
        total_duration = sum(log.duration_minutes or 0 for log in logs)
        avg_rating = (
            sum(log.rating or 0 for log in logs) / total_workouts
            if total_workouts > 0
            else 0
        )

        return success_response(
            {
                "period_days": period,
                "total_workouts": total_workouts,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": total_duration / total_workouts
                if total_workouts > 0
                else 0,
                "average_rating": round(avg_rating, 1),
                "workout_frequency_per_week": round((total_workouts / period) * 7, 1),
            },
            "Workout statistics retrieved successfully",
            200,
        )

    except Exception as e:
        return error_response("Failed to retrieve workout statistics", 500, str(e))


# ============================================
# Calendar Integration (iCal / Subscription feed)
# ============================================


@workouts_bp.route("/calendar/feed-info", methods=["GET"])
@jwt_required()
def get_calendar_feed_info():
    """
    Return subscription URLs so the user can wire their FitApp workouts into
    Google Calendar, Apple Calendar, Outlook, or any iCal-compatible client.
    GET /api/workouts/calendar/feed-info
    """
    try:
        user_id = int(get_jwt_identity())
        token = _make_feed_token(user_id)

        # Build an absolute URL to the .ics feed. host_url already ends with '/'.
        host = request.host_url.rstrip("/")
        feed_url = f"{host}/api/workouts/calendar.ics?token={token}"

        # webcal:// is the subscribe-as-live-calendar protocol supported by
        # Apple Calendar, Outlook (desktop), and most mobile calendar apps.
        webcal_url = feed_url.replace("https://", "webcal://").replace(
            "http://", "webcal://"
        )

        # Google Calendar "Add by URL" entry point
        from urllib.parse import quote

        google_calendar_url = (
            f"https://calendar.google.com/calendar/r?cid={quote(webcal_url, safe='')}"
        )

        # Outlook Web "Add from web" entry point
        outlook_url = (
            "https://outlook.live.com/calendar/0/addfromweb?"
            f"url={quote(feed_url, safe='')}&name={quote('FitApp Workouts', safe='')}"
        )

        return success_response(
            {
                "feed_url": feed_url,
                "webcal_url": webcal_url,
                "google_calendar_url": google_calendar_url,
                "outlook_url": outlook_url,
                "token": token,
                "instructions": {
                    "apple": "Click the Apple Calendar button (uses webcal://) or in Calendar choose File → New Calendar Subscription and paste the feed URL.",
                    "google": 'Click the Google Calendar button, or in Google Calendar choose "Other calendars" → "From URL" and paste the feed URL.',
                    "outlook": 'Click the Outlook button, or in Outlook choose "Add calendar" → "Subscribe from web" and paste the feed URL.',
                    "download": "Download the .ics file to import a one-time snapshot of your workouts into any calendar app.",
                },
            },
            "Calendar feed info retrieved successfully",
            200,
        )

    except Exception as e:
        import traceback

        print(f"\n===== ERROR in GET /calendar/feed-info =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to build calendar feed info", 500, str(e))


@workouts_bp.route("/calendar.ics", methods=["GET"])
def workout_calendar_ics():
    """
    Serve the user's workout schedule as an iCalendar feed.
    GET /api/workouts/calendar.ics?token=<signed>
    Also accepts an Authorization: Bearer <jwt> header as a fallback so the
    frontend can stream a download without exposing the subscription token.
    """
    try:
        user_id = None

        # 1) Signed subscription token — used by Apple / Google / Outlook clients
        token = request.args.get("token")
        if token:
            user_id = _parse_feed_token(token)

        # 2) JWT header — used by the authenticated "Download .ics" button
        if user_id is None:
            try:
                from flask_jwt_extended import (
                    verify_jwt_in_request,
                    get_jwt_identity as _get_jwt_identity,
                )

                verify_jwt_in_request(optional=True)
                ident = _get_jwt_identity()
                if ident is not None:
                    user_id = int(ident)
            except Exception:
                user_id = None

        if user_id is None:
            return error_response("Invalid or missing calendar token", 401)

        ics = _build_workout_ics(user_id, request.host_url)

        resp = Response(ics, mimetype="text/calendar; charset=utf-8")
        resp.headers["Content-Disposition"] = (
            'attachment; filename="fitapp-workouts.ics"'
        )
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

    except Exception as e:
        import traceback

        print(f"\n===== ERROR in GET /calendar.ics =====")
        print(f"Exception: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        print(f"==============================\n")
        return error_response("Failed to build calendar feed", 500, str(e))
