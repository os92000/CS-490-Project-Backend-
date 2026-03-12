"""
Phase 11: Security & Performance
Performance optimization utilities
"""
from functools import wraps
from flask import request
import time
import logging

logger = logging.getLogger(__name__)

def log_slow_requests(threshold_seconds=1.0):
    """
    Log requests that take longer than threshold

    Args:
        threshold_seconds: Time threshold in seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time

            if duration > threshold_seconds:
                logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")

            return result
        return wrapped
    return decorator

def cache_response(timeout=300):
    """
    Simple response caching decorator (use Redis in production)

    Args:
        timeout: Cache timeout in seconds
    """
    cache = {}

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Create cache key from request path and args
            cache_key = f"{request.path}:{request.args}"
            current_time = time.time()

            # Check cache
            if cache_key in cache:
                cached_data, timestamp = cache[cache_key]
                if current_time - timestamp < timeout:
                    return cached_data

            # Execute function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = (result, current_time)

            return result
        return wrapped
    return decorator

def optimize_query(query, limit=100):
    """
    Optimize database queries with pagination

    Args:
        query: SQLAlchemy query object
        limit: Maximum number of results

    Returns:
        Optimized query
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), limit)

    return query.paginate(page=page, per_page=per_page, error_out=False)
