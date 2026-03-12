"""
Phase 11: Security & Performance
Security middleware and utilities
"""
from functools import wraps
from flask import request, jsonify
import time

# Rate limiting storage (simple in-memory, use Redis in production)
rate_limit_store = {}

def rate_limit(max_requests=100, window_seconds=60):
    """
    Rate limiting decorator

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get client identifier
            client_id = request.remote_addr
            current_time = time.time()

            # Initialize or clean old entries
            if client_id not in rate_limit_store:
                rate_limit_store[client_id] = []

            # Remove old timestamps outside the window
            rate_limit_store[client_id] = [
                timestamp for timestamp in rate_limit_store[client_id]
                if current_time - timestamp < window_seconds
            ]

            # Check rate limit
            if len(rate_limit_store[client_id]) >= max_requests:
                return jsonify({
                    'success': False,
                    'data': None,
                    'message': 'Rate limit exceeded',
                    'error': 'too_many_requests'
                }), 429

            # Add current timestamp
            rate_limit_store[client_id].append(current_time)

            return f(*args, **kwargs)
        return wrapped
    return decorator

def sanitize_input(data):
    """
    Sanitize user input to prevent XSS and injection attacks

    Args:
        data: Input data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Basic XSS prevention
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            data = data.replace(char, '')
        return data.strip()
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def validate_file_upload(file, allowed_extensions={'jpg', 'jpeg', 'png', 'gif'}):
    """
    Validate uploaded files

    Args:
        file: FileStorage object
        allowed_extensions: Set of allowed file extensions

    Returns:
        Boolean indicating if file is valid
    """
    if not file or not file.filename:
        return False

    extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    return extension in allowed_extensions

def secure_headers():
    """
    Add security headers to responses
    This should be applied as an after_request handler in app.py
    """
    def add_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    return add_headers
