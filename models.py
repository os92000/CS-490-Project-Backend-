from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and role management"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('client', 'coach', 'both', 'admin', name='user_roles'), nullable=True)
    status = db.Column(db.Enum('active', 'disabled', name='user_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    fitness_survey = db.relationship('FitnessSurvey', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_profile=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_profile and self.profile:
            data['profile'] = self.profile.to_dict()
        return data

    def __repr__(self):
        return f'<User {self.email}>'


class UserProfile(db.Model):
    """User profile information"""
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))

    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'phone': self.phone
        }

    def __repr__(self):
        return f'<UserProfile {self.first_name} {self.last_name}>'


class FitnessSurvey(db.Model):
    """Initial fitness survey responses"""
    __tablename__ = 'fitness_surveys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    weight = db.Column(db.Numeric(5, 2))  # in kg
    age = db.Column(db.Integer)
    fitness_level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='fitness_levels'))
    goals = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert survey to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weight': float(self.weight) if self.weight else None,
            'age': self.age,
            'fitness_level': self.fitness_level,
            'goals': self.goals,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<FitnessSurvey user_id={self.user_id}>'


class RoleChangeRequest(db.Model):
    """
    A user's request to change their role (e.g., client wanting to become a coach).
    Must be approved by an admin before the user's role is updated.
    """
    __tablename__ = 'role_change_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    current_role = db.Column(db.String(20))
    requested_role = db.Column(db.Enum('coach', 'both', name='requested_role_enum'), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(
        db.Enum('pending', 'approved', 'rejected', name='role_request_status'),
        default='pending',
        nullable=False,
        index=True
    )
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))

    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('role_change_requests', cascade='all, delete-orphan')
    )
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'current_role': self.current_role,
            'requested_role': self.requested_role,
            'reason': self.reason,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by,
        }
        if include_user and self.user:
            data['user_email'] = self.user.email
            data['user_name'] = None
            if self.user.profile:
                first = self.user.profile.first_name or ''
                last = self.user.profile.last_name or ''
                full = f'{first} {last}'.strip()
                data['user_name'] = full or None
        return data

    def __repr__(self):
        return f'<RoleChangeRequest user_id={self.user_id} {self.current_role}->{self.requested_role} {self.status}>'


# ============================================
# PHASE 2: Coach Marketplace Models
# ============================================

class Specialization(db.Model):
    """Coach specializations (e.g., Weight Loss, Muscle Gain, etc.)"""
    __tablename__ = 'specializations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category
        }

    def __repr__(self):
        return f'<Specialization {self.name}>'


class CoachSurvey(db.Model):
    """Coach profile information"""
    __tablename__ = 'coach_surveys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    experience_years = db.Column(db.Integer)
    certifications = db.Column(db.Text)
    bio = db.Column(db.Text)
    specialization_notes = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', backref='coach_survey')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'experience_years': self.experience_years,
            'certifications': self.certifications,
            'bio': self.bio,
            'specialization_notes': self.specialization_notes
        }

    def __repr__(self):
        return f'<CoachSurvey user_id={self.user_id}>'


class CoachSpecialization(db.Model):
    """Many-to-many relationship between coaches and specializations"""
    __tablename__ = 'coach_specializations'

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specializations.id'), nullable=False)

    # Relationships
    coach = db.relationship('User', backref='coach_specializations')
    specialization = db.relationship('Specialization', backref='coach_specializations')

    def to_dict(self):
        return {
            'id': self.id,
            'coach_id': self.coach_id,
            'specialization_id': self.specialization_id,
            'specialization': self.specialization.to_dict() if self.specialization else None
        }

    def __repr__(self):
        return f'<CoachSpecialization coach_id={self.coach_id} spec_id={self.specialization_id}>'


class CoachAvailability(db.Model):
    """Coach availability schedule"""
    __tablename__ = 'coach_availability'

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Relationships
    coach = db.relationship('User', backref='availability_slots')

    def to_dict(self):
        return {
            'id': self.id,
            'coach_id': self.coach_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None
        }

    def __repr__(self):
        return f'<CoachAvailability coach_id={self.coach_id} day={self.day_of_week}>'


class CoachPricing(db.Model):
    """Coach pricing information"""
    __tablename__ = 'coach_pricing'

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_type = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')

    # Relationships
    coach = db.relationship('User', backref='pricing')

    def to_dict(self):
        return {
            'id': self.id,
            'coach_id': self.coach_id,
            'session_type': self.session_type,
            'price': float(self.price) if self.price else None,
            'currency': self.currency
        }

    def __repr__(self):
        return f'<CoachPricing coach_id={self.coach_id} type={self.session_type}>'


class ClientRequest(db.Model):
    """Client requests to hire a coach"""
    __tablename__ = 'client_requests'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'denied', name='request_status'), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)

    # Relationships
    client = db.relationship('User', foreign_keys=[client_id], backref='sent_requests')
    coach = db.relationship('User', foreign_keys=[coach_id], backref='received_requests')

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'coach_id': self.coach_id,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }

    def __repr__(self):
        return f'<ClientRequest client={self.client_id} coach={self.coach_id} status={self.status}>'


class CoachApplication(db.Model):
    """Coach application workflow for admin approval"""
    __tablename__ = 'coach_applications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'denied', name='coach_application_status'), default='pending')
    notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    user = db.relationship('User', foreign_keys=[user_id], backref='coach_application')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'notes': self.notes,
            'reviewed_by': self.reviewed_by,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'user': self.user.to_dict(include_profile=True) if self.user else None
        }


class ModerationReport(db.Model):
    """Coach and chat reporting for admin moderation"""
    __tablename__ = 'moderation_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.Enum('coach', 'chat', name='moderation_report_type'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    relationship_id = db.Column(db.Integer, db.ForeignKey('coach_relationships.id', ondelete='CASCADE'))
    reason = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.Enum('open', 'reviewed', 'resolved', 'dismissed', name='moderation_report_status'), default='open')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_created')
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], backref='reports_received')
    relationship = db.relationship('CoachRelationship', backref='moderation_reports')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'reporter_id': self.reporter_id,
            'reported_user_id': self.reported_user_id,
            'relationship_id': self.relationship_id,
            'reason': self.reason,
            'details': self.details,
            'status': self.status,
            'reviewed_by': self.reviewed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reporter': self.reporter.to_dict(include_profile=True) if self.reporter else None,
            'reported_user': self.reported_user.to_dict(include_profile=True) if self.reported_user else None
        }


class CoachRelationship(db.Model):
    """Active client-coach relationships"""
    __tablename__ = 'coach_relationships'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('active', 'ended', name='relationship_status'), default='active')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)

    # Relationships
    client = db.relationship('User', foreign_keys=[client_id], backref='client_relationships')
    coach = db.relationship('User', foreign_keys=[coach_id], backref='coach_relationships')

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'coach_id': self.coach_id,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }

    def __repr__(self):
        return f'<CoachRelationship client={self.client_id} coach={self.coach_id} status={self.status}>'


class Review(db.Model):
    """Coach reviews from clients"""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    client = db.relationship('User', foreign_keys=[client_id], backref='reviews_written')
    coach = db.relationship('User', foreign_keys=[coach_id], backref='reviews_received')

    def to_dict(self, include_client=False):
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'coach_id': self.coach_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_client and self.client:
            data['client'] = {
                'id': self.client.id,
                'email': self.client.email,
                'profile': self.client.profile.to_dict() if self.client.profile else None
            }
        return data

    def __repr__(self):
        return f'<Review coach={self.coach_id} rating={self.rating}>'


# ============================================
# PHASE 3: Chat/Messaging Models
# ============================================

class ChatMessage(db.Model):
    """Chat messages between client and coach"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    relationship_id = db.Column(db.Integer, db.ForeignKey('coach_relationships.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    # Relationships
    relationship = db.relationship('CoachRelationship', backref='messages')
    sender = db.relationship('User', backref='sent_messages')

    def to_dict(self, include_sender=False):
        data = {
            'id': self.id,
            'relationship_id': self.relationship_id,
            'sender_id': self.sender_id,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
        if include_sender and self.sender:
            data['sender'] = {
                'id': self.sender.id,
                'email': self.sender.email,
                'profile': self.sender.profile.to_dict() if self.sender.profile else None
            }
        return data

    def __repr__(self):
        return f'<ChatMessage relationship={self.relationship_id} sender={self.sender_id}>'


# ============================================
# PHASE 4: Workout Management Models
# ============================================

class Exercise(db.Model):
    """Exercise database with details for each exercise"""
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.Enum('cardio', 'strength', 'flexibility', 'balance', 'sports', name='exercise_categories'))
    muscle_group = db.Column(db.String(100))  # e.g., "chest", "legs", "back", etc.
    equipment = db.Column(db.String(100))  # e.g., "dumbbells", "bodyweight", "machine"
    difficulty = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='exercise_difficulty'))
    video_url = db.Column(db.String(255))
    instructions = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # NULL for default exercises, user_id for custom
    is_public = db.Column(db.Boolean, default=True)  # Public exercises vs. coach-specific
    # Workout library fields
    calories = db.Column(db.Integer)  # Estimated calories burned for a default session
    default_duration_minutes = db.Column(db.Integer)  # Typical duration of the workout
    is_library_workout = db.Column(db.Boolean, default=False)  # True = complete workout in the library, False = movement/component
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', backref='created_exercises')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'muscle_group': self.muscle_group,
            'equipment': self.equipment,
            'difficulty': self.difficulty,
            'video_url': self.video_url,
            'instructions': self.instructions,
            'created_by': self.created_by,
            'is_public': self.is_public,
            'calories': self.calories,
            'default_duration_minutes': self.default_duration_minutes,
            'is_library_workout': bool(self.is_library_workout),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Exercise {self.name}>'


class WorkoutPlan(db.Model):
    """Workout plans — created by a coach for a client, or by a client for themselves"""
    __tablename__ = 'workout_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # coach_id is NULL when a client creates their own plan
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.Enum('active', 'completed', 'archived', name='plan_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    coach = db.relationship('User', foreign_keys=[coach_id], backref='plans_created')
    client = db.relationship('User', foreign_keys=[client_id], backref='workout_plans')

    def to_dict(self, include_days=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'coach_id': self.coach_id,
            'client_id': self.client_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_days:
            data['days'] = [day.to_dict(include_exercises=True) for day in self.workout_days]
        return data

    def __repr__(self):
        return f'<WorkoutPlan {self.name}>'


class WorkoutPlanMetadata(db.Model):
    """Optional metadata used for plan filtering"""
    __tablename__ = 'workout_plan_metadata'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id', ondelete='CASCADE'), unique=True, nullable=False)
    goal = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    plan_type = db.Column(db.String(50))
    duration_weeks = db.Column(db.Integer)

    plan = db.relationship('WorkoutPlan', backref='metadata_record')

    def to_dict(self):
        return {
            'goal': self.goal,
            'difficulty': self.difficulty,
            'plan_type': self.plan_type,
            'duration_weeks': self.duration_weeks
        }


class WorkoutTemplate(db.Model):
    """Prebuilt workout template that can be customized into a plan"""
    __tablename__ = 'workout_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    goal = db.Column(db.String(100))
    difficulty = db.Column(db.String(50))
    plan_type = db.Column(db.String(50))
    duration_weeks = db.Column(db.Integer)
    template_data = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_public = db.Column(db.Boolean, default=True)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref='workout_templates')

    def to_dict(self):
        try:
            data = json.loads(self.template_data or '{}')
        except Exception:
            data = {}

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'goal': self.goal,
            'difficulty': self.difficulty,
            'plan_type': self.plan_type,
            'duration_weeks': self.duration_weeks,
            'template_data': data,
            'created_by': self.created_by,
            'is_public': self.is_public,
            'approved': self.approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkoutPlanAssignment(db.Model):
    """Explicit calendar assignments for workout plans"""
    __tablename__ = 'workout_plan_assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id', ondelete='CASCADE'), nullable=False)
    workout_day_id = db.Column(db.Integer, db.ForeignKey('workout_days.id', ondelete='SET NULL'))
    assigned_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='workout_assignments')
    plan = db.relationship('WorkoutPlan', backref='assignments')
    workout_day = db.relationship('WorkoutDay', backref='assignments')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'workout_day_id': self.workout_day_id,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'plan': self.plan.to_dict() if self.plan else None,
            'workout_day': self.workout_day.to_dict() if self.workout_day else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkoutDay(db.Model):
    """Individual days in a workout plan"""
    __tablename__ = 'workout_days'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # e.g., "Day 1: Upper Body"
    day_number = db.Column(db.Integer)  # Order in the plan
    notes = db.Column(db.Text)

    # Relationships
    plan = db.relationship('WorkoutPlan', backref='workout_days')

    def to_dict(self, include_exercises=False):
        data = {
            'id': self.id,
            'plan_id': self.plan_id,
            'name': self.name,
            'day_number': self.day_number,
            'notes': self.notes
        }
        if include_exercises:
            data['exercises'] = [ex.to_dict() for ex in self.plan_exercises]
        return data

    def __repr__(self):
        return f'<WorkoutDay {self.name}>'


class PlanExercise(db.Model):
    """Exercises assigned to a workout day with sets, reps, etc."""
    __tablename__ = 'plan_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_day_id = db.Column(db.Integer, db.ForeignKey('workout_days.id', ondelete='CASCADE'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    order = db.Column(db.Integer)  # Order in the workout day
    sets = db.Column(db.Integer)
    reps = db.Column(db.String(50))  # String to allow "8-12" or "AMRAP"
    duration_minutes = db.Column(db.Integer)  # For cardio/timed exercises
    rest_seconds = db.Column(db.Integer)
    weight = db.Column(db.String(50))  # String to allow "bodyweight" or "20kg"
    notes = db.Column(db.Text)

    # Relationships
    workout_day = db.relationship('WorkoutDay', backref='plan_exercises')
    exercise = db.relationship('Exercise', backref='plan_assignments')

    def to_dict(self):
        return {
            'id': self.id,
            'workout_day_id': self.workout_day_id,
            'exercise_id': self.exercise_id,
            'exercise': self.exercise.to_dict() if self.exercise else None,
            'order': self.order,
            'sets': self.sets,
            'reps': self.reps,
            'duration_minutes': self.duration_minutes,
            'rest_seconds': self.rest_seconds,
            'weight': self.weight,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<PlanExercise exercise_id={self.exercise_id}>'


class WorkoutLog(db.Model):
    """Client workout logs - tracking actual completed workouts"""
    __tablename__ = 'workout_logs'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id', ondelete='SET NULL'))
    workout_day_id = db.Column(db.Integer, db.ForeignKey('workout_days.id', ondelete='SET NULL'))
    # Library-backed or custom workout fields
    library_exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id', ondelete='SET NULL'))
    workout_name = db.Column(db.String(200))
    calories_burned = db.Column(db.Integer)
    exercise_type = db.Column(db.String(50))  # Mirrors Exercise.category for ad-hoc logs
    muscle_group = db.Column(db.String(100))
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 how the workout felt
    completed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    client = db.relationship('User', backref='workout_logs')
    plan = db.relationship('WorkoutPlan', backref='logs')
    workout_day = db.relationship('WorkoutDay', backref='logs')
    library_exercise = db.relationship('Exercise', foreign_keys=[library_exercise_id])

    def to_dict(self, include_exercises=False):
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'plan_id': self.plan_id,
            'workout_day_id': self.workout_day_id,
            'library_exercise_id': self.library_exercise_id,
            'workout_name': self.workout_name,
            'calories_burned': self.calories_burned,
            'exercise_type': self.exercise_type,
            'muscle_group': self.muscle_group,
            'date': self.date.isoformat() if self.date else None,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'rating': self.rating,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_exercises:
            data['exercise_logs'] = [ex.to_dict() for ex in self.exercise_logs]
        if self.workout_day:
            data['workout_day'] = self.workout_day.to_dict()
        if self.library_exercise:
            data['library_exercise'] = self.library_exercise.to_dict()
        return data

    def __repr__(self):
        return f'<WorkoutLog client={self.client_id} date={self.date}>'


class ExerciseLog(db.Model):
    """Individual exercise performance within a workout log"""
    __tablename__ = 'exercise_logs'

    id = db.Column(db.Integer, primary_key=True)
    workout_log_id = db.Column(db.Integer, db.ForeignKey('workout_logs.id', ondelete='CASCADE'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    sets_completed = db.Column(db.Integer)
    reps_completed = db.Column(db.String(50))  # JSON or comma-separated: "10,10,8"
    weight_used = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)

    # Relationships
    workout_log = db.relationship('WorkoutLog', backref='exercise_logs')
    exercise = db.relationship('Exercise', backref='exercise_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'workout_log_id': self.workout_log_id,
            'exercise_id': self.exercise_id,
            'exercise': self.exercise.to_dict() if self.exercise else None,
            'sets_completed': self.sets_completed,
            'reps_completed': self.reps_completed,
            'weight_used': self.weight_used,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<ExerciseLog exercise_id={self.exercise_id}>'


# ============================================
# PHASE 5: Nutrition & Wellness Models
# ============================================

class MealLog(db.Model):
    """Daily meal logging"""
    __tablename__ = 'meal_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.Enum('breakfast', 'lunch', 'dinner', 'snack', name='meal_types'))
    food_items = db.Column(db.Text)  # JSON or comma-separated
    calories = db.Column(db.Integer)
    protein_g = db.Column(db.Numeric(6, 2))
    carbs_g = db.Column(db.Numeric(6, 2))
    fat_g = db.Column(db.Numeric(6, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='meal_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'meal_type': self.meal_type,
            'food_items': self.food_items,
            'calories': self.calories,
            'protein_g': float(self.protein_g) if self.protein_g else None,
            'carbs_g': float(self.carbs_g) if self.carbs_g else None,
            'fat_g': float(self.fat_g) if self.fat_g else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<MealLog user={self.user_id} date={self.date}>'


class BodyMetric(db.Model):
    """Body measurements and metrics tracking"""
    __tablename__ = 'body_metrics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight_kg = db.Column(db.Numeric(5, 2))
    body_fat_percentage = db.Column(db.Numeric(4, 2))
    muscle_mass_kg = db.Column(db.Numeric(5, 2))
    chest_cm = db.Column(db.Numeric(5, 2))
    waist_cm = db.Column(db.Numeric(5, 2))
    hips_cm = db.Column(db.Numeric(5, 2))
    arms_cm = db.Column(db.Numeric(5, 2))
    thighs_cm = db.Column(db.Numeric(5, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='body_metrics')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'body_fat_percentage': float(self.body_fat_percentage) if self.body_fat_percentage else None,
            'muscle_mass_kg': float(self.muscle_mass_kg) if self.muscle_mass_kg else None,
            'chest_cm': float(self.chest_cm) if self.chest_cm else None,
            'waist_cm': float(self.waist_cm) if self.waist_cm else None,
            'hips_cm': float(self.hips_cm) if self.hips_cm else None,
            'arms_cm': float(self.arms_cm) if self.arms_cm else None,
            'thighs_cm': float(self.thighs_cm) if self.thighs_cm else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<BodyMetric user={self.user_id} date={self.date}>'


class WellnessLog(db.Model):
    """Daily wellness tracking (mood, sleep, etc.)"""
    __tablename__ = 'wellness_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    mood = db.Column(db.Enum('excellent', 'good', 'okay', 'poor', 'terrible', name='mood_levels'))
    energy_level = db.Column(db.Integer)  # 1-10
    stress_level = db.Column(db.Integer)  # 1-10
    sleep_hours = db.Column(db.Numeric(4, 2))
    sleep_quality = db.Column(db.Enum('excellent', 'good', 'fair', 'poor', name='sleep_quality'))
    water_intake_ml = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='wellness_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'mood': self.mood,
            'energy_level': self.energy_level,
            'stress_level': self.stress_level,
            'sleep_hours': float(self.sleep_hours) if self.sleep_hours else None,
            'sleep_quality': self.sleep_quality,
            'water_intake_ml': self.water_intake_ml,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<WellnessLog user={self.user_id} date={self.date}>'


class DailyMetric(db.Model):
    """Daily activity metrics like steps and water"""
    __tablename__ = 'daily_metrics'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    steps = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    water_intake_ml = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='daily_metrics')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'steps': self.steps,
            'calories_burned': self.calories_burned,
            'water_intake_ml': self.water_intake_ml,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MealPlan(db.Model):
    """Simple meal plan records"""
    __tablename__ = 'meal_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='meal_plans')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================
# PHASE 10: Profile Management
# ============================================

class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(50))
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Notification {self.id}>'


class PaymentRecord(db.Model):
    """Mock payment records used for payment history and analytics"""
    __tablename__ = 'payment_records'

    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    payment_reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(30), default='completed')
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payer = db.relationship('User', foreign_keys=[payer_id], backref='payments_made')
    coach = db.relationship('User', foreign_keys=[coach_id], backref='payments_received')

    def to_dict(self):
        try:
            metadata = json.loads(self.metadata_json or '{}')
        except Exception:
            metadata = {}

        return {
            'id': self.id,
            'payer_id': self.payer_id,
            'coach_id': self.coach_id,
            'payment_reference': self.payment_reference,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'metadata': metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
