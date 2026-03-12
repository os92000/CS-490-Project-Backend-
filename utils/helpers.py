import os
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image

def generate_random_filename(original_filename):
    """Generate a random filename while preserving extension"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    random_name = secrets.token_hex(16)
    return f"{random_name}.{ext}"

def save_uploaded_file(file, upload_folder, resize=None):
    """
    Save uploaded file with a secure random name
    Args:
        file: FileStorage object
        upload_folder: Target directory
        resize: Optional tuple (width, height) to resize images
    Returns:
        filename: Saved filename
    """
    # Create upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)

    # Generate secure filename
    original_filename = secure_filename(file.filename)
    filename = generate_random_filename(original_filename)
    filepath = os.path.join(upload_folder, filename)

    # Save the file
    file.save(filepath)

    # Resize image if specified
    if resize:
        try:
            with Image.open(filepath) as img:
                img.thumbnail(resize, Image.LANCZOS)
                img.save(filepath)
        except Exception as e:
            print(f"Error resizing image: {e}")

    return filename

def delete_file(filepath):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
    return False

def paginate_query(query, page, per_page, max_per_page=100):
    """
    Paginate a SQLAlchemy query
    Returns: (items, total, pages, current_page)
    """
    per_page = min(per_page, max_per_page)
    page = max(1, page)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': paginated.items,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'per_page': per_page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev
    }

def success_response(data=None, message="Success", status_code=200):
    """Standard success response format"""
    return {
        'success': True,
        'data': data,
        'message': message,
        'error': None
    }, status_code

def error_response(message="An error occurred", status_code=400, error_details=None):
    """Standard error response format"""
    return {
        'success': False,
        'data': None,
        'message': message,
        'error': error_details
    }, status_code

def is_current_day(date_obj):
    """Check if a datetime/date object is today"""
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    return date_obj == datetime.utcnow().date()

def get_date_range(period):
    """
    Get start and end dates for a period
    Args:
        period: 'day', 'week', 'month', 'year'
    Returns:
        (start_date, end_date)
    """
    end_date = datetime.utcnow()

    if period == 'day':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)  # Default to month

    return start_date, end_date
