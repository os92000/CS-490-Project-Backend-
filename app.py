import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from sqlalchemy import inspect, text
from config import config
from models import db

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app,
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    jwt = JWTManager(app)
    socketio.init_app(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.users_routes import users_bp
    from routes.surveys_routes import surveys_bp
    from routes.coaches_routes import coaches_bp
    from routes.chat_routes import chat_bp, init_socketio_events
    from routes.workouts_routes import workouts_bp
    from routes.nutrition_routes import nutrition_bp
    from routes.profile_routes import profile_bp
    from routes.analytics_routes import analytics_bp
    from routes.admin_routes import admin_bp
    from routes.payments_routes import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(surveys_bp)
    app.register_blueprint(coaches_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payments_bp)

    # Initialize WebSocket event handlers
    init_socketio_events(socketio)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Resource not found',
            'error': str(error)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Internal server error',
            'error': str(error)
        }), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Bad request',
            'error': str(error)
        }), 400

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Token has expired',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Invalid token',
            'error': str(error)
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'success': False,
            'data': None,
            'message': 'Authorization token is missing',
            'error': str(error)
        }), 401

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'environment': config_name
            },
            'message': 'Application is running',
            'error': None
        }), 200

    # API root endpoint
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'success': True,
            'data': {
                'name': 'Fitness App API',
                'version': '1.0.0',
                'endpoints': {
                    'auth': '/api/auth',
                    'users': '/api/users',
                    'surveys': '/api/surveys',
                    'coaches': '/api/coaches',
                    'chat': '/api/chat',
                    'workouts': '/api/workouts',
                    'nutrition': '/api/nutrition',
                    'profile': '/api/profile',
                    'analytics': '/api/analytics',
                    'admin': '/api/admin',
                    'payments': '/api/payments'
                }
            },
            'message': 'Welcome to Fitness App API',
            'error': None
        }), 200

    # Create database tables
    with app.app_context():
        db.create_all()
        ensure_schema_updates()

    return app

def ensure_schema_updates():
    """Apply small additive schema updates for existing databases."""
    dialect = db.engine.dialect.name
    inspector = inspect(db.engine)

    def ensure_columns(table_name, column_definitions):
        if not inspector.has_table(table_name):
            return set()

        existing_columns = {
            column['name'] for column in inspector.get_columns(table_name)
        }

        for column_name, definitions in column_definitions.items():
            if column_name in existing_columns:
                continue

            column_type = definitions.get(dialect, definitions['default'])
            db.session.execute(
                text(
                    f'ALTER TABLE {table_name} '
                    f'ADD COLUMN `{column_name}` {column_type}'
                )
            )
            existing_columns.add(column_name)

        return existing_columns

    ensure_columns('coach_applications', {
        'notes': {
            'sqlite': 'TEXT',
            'default': 'TEXT'
        },
        'reviewed_by': {
            'sqlite': 'INTEGER',
            'default': 'INTEGER'
        },
        'submitted_at': {
            'sqlite': 'DATETIME',
            'default': 'DATETIME'
        },
        'reviewed_at': {
            'sqlite': 'DATETIME',
            'default': 'DATETIME'
        }
    })

    ensure_columns('workout_logs', {
        'library_exercise_id': {
            'sqlite': 'INTEGER',
            'default': 'INTEGER'
        },
        'workout_name': {
            'sqlite': 'VARCHAR(200)',
            'default': 'VARCHAR(200)'
        },
        'calories_burned': {
            'sqlite': 'INTEGER',
            'default': 'INTEGER'
        },
        'exercise_type': {
            'sqlite': 'VARCHAR(50)',
            'default': 'VARCHAR(50)'
        },
        'muscle_group': {
            'sqlite': 'VARCHAR(100)',
            'default': 'VARCHAR(100)'
        }
    })

    ensure_columns('exercises', {
        'calories': {
            'sqlite': 'INTEGER',
            'default': 'INTEGER'
        },
        'default_duration_minutes': {
            'sqlite': 'INTEGER',
            'default': 'INTEGER'
        },
        'is_library_workout': {
            'sqlite': 'BOOLEAN',
            'default': 'BOOLEAN'
        }
    })

    daily_metric_columns = ensure_columns('daily_metrics', {
        'date': {
            'sqlite': 'DATE',
            'default': 'DATE'
        },
        'notes': {
            'sqlite': 'TEXT',
            'default': 'TEXT'
        }
    })
    if {'date', 'log_date'}.issubset(daily_metric_columns):
        db.session.execute(text(
            'UPDATE daily_metrics SET date = log_date WHERE date IS NULL'
        ))

    meal_plan_columns = ensure_columns('meal_plans', {
        'title': {
            'sqlite': 'VARCHAR(200)',
            'default': 'VARCHAR(200)'
        },
        'notes': {
            'sqlite': 'TEXT',
            'default': 'TEXT'
        }
    })
    if {'title', 'name'}.issubset(meal_plan_columns):
        db.session.execute(text(
            'UPDATE meal_plans SET title = name WHERE title IS NULL OR title = ""'
        ))

    notification_columns = ensure_columns('notifications', {
        'read': {
            'sqlite': 'BOOLEAN',
            'default': 'BOOLEAN'
        }
    })
    if {'read', 'read_status'}.issubset(notification_columns):
        db.session.execute(text(
            'UPDATE notifications SET `read` = read_status WHERE `read` IS NULL'
        ))

    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
