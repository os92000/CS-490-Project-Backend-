"""
Create (or update) an admin user.

Usage:
    python create_admin.py
    python create_admin.py <email> <password>
    python create_admin.py <email> <password> <first_name> <last_name>

If the email already exists, the user is promoted to admin and the
password is reset to the value provided.
"""
import sys
from app import create_app
from models import db, User, UserProfile

DEFAULT_EMAIL = 'admin@fitness.app'
DEFAULT_PASSWORD = 'Admin123!'
DEFAULT_FIRST_NAME = 'Site'
DEFAULT_LAST_NAME = 'Admin'


def create_admin(email, password, first_name, last_name):
    email = email.strip().lower()

    user = User.query.filter_by(email=email).first()
    if user:
        user.role = 'admin'
        user.status = 'active'
        user.set_password(password)

        if not user.profile:
            user.profile = UserProfile(
                first_name=first_name,
                last_name=last_name,
            )
        else:
            if not user.profile.first_name:
                user.profile.first_name = first_name
            if not user.profile.last_name:
                user.profile.last_name = last_name

        db.session.commit()
        print(f"Existing user '{email}' promoted to admin and password reset.")
    else:
        user = User(email=email, role='admin', status='active')
        user.set_password(password)
        user.profile = UserProfile(
            first_name=first_name,
            last_name=last_name,
        )
        db.session.add(user)
        db.session.commit()
        print(f"New admin user '{email}' created.")

    print("---- Admin credentials ----")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"Role:     {user.role}")
    print(f"User ID:  {user.id}")


if __name__ == '__main__':
    args = sys.argv[1:]
    email = args[0] if len(args) >= 1 else DEFAULT_EMAIL
    password = args[1] if len(args) >= 2 else DEFAULT_PASSWORD
    first_name = args[2] if len(args) >= 3 else DEFAULT_FIRST_NAME
    last_name = args[3] if len(args) >= 4 else DEFAULT_LAST_NAME

    app = create_app()
    with app.app_context():
        create_admin(email, password, first_name, last_name)
