"""
Create a set of test accounts for development and QA.

Usage:
    python create_test_accounts.py

Creates (if they don't already exist):
    - 1 admin account
    - 5 coach accounts (with profile, coach survey, specializations, pricing)
    - 5 client accounts (with profile)

All accounts share the same password: TestPass1!
(Meets: 8+ chars, uppercase, lowercase, digit.)

Re-running is safe: existing emails are skipped, not modified.
"""
from app import create_app
from models import (
    db,
    User,
    UserProfile,
    CoachSurvey,
    CoachSpecialization,
    CoachPricing,
    Specialization,
)


PASSWORD = 'TestPass1!'


ADMIN_ACCOUNT = {
    'email': 'admin@test.fit',
    'first_name': 'Test',
    'last_name': 'Admin',
}

TEST_COACHES = [
    {
        'email': 'coach1@test.fit',
        'first_name': 'Test',
        'last_name': 'CoachOne',
        'phone': '+1-555-1001',
        'bio': 'Generic test coach #1 for QA and development.',
        'experience_years': 5,
        'certifications': 'Test Certification A',
        'coach_bio': 'Test coach bio for coach #1.',
        'specialization_notes': 'General fitness',
        'specializations': ['Strength Training'],
        'pricing': [('1-on-1 Session', 50.00), ('Monthly Package', 180.00)],
    },
    {
        'email': 'coach2@test.fit',
        'first_name': 'Test',
        'last_name': 'CoachTwo',
        'phone': '+1-555-1002',
        'bio': 'Generic test coach #2 for QA and development.',
        'experience_years': 3,
        'certifications': 'Test Certification B',
        'coach_bio': 'Test coach bio for coach #2.',
        'specialization_notes': 'Cardio and endurance',
        'specializations': ['Cardio Training'],
        'pricing': [('1-on-1 Session', 45.00), ('Group Session', 20.00)],
    },
    {
        'email': 'coach3@test.fit',
        'first_name': 'Test',
        'last_name': 'CoachThree',
        'phone': '+1-555-1003',
        'bio': 'Generic test coach #3 for QA and development.',
        'experience_years': 7,
        'certifications': 'Test Certification C',
        'coach_bio': 'Test coach bio for coach #3.',
        'specialization_notes': 'Weight loss programs',
        'specializations': ['Weight Loss', 'Nutrition Coaching'],
        'pricing': [('1-on-1 Session', 60.00), ('Monthly Package', 220.00)],
    },
    {
        'email': 'coach4@test.fit',
        'first_name': 'Test',
        'last_name': 'CoachFour',
        'phone': '+1-555-1004',
        'bio': 'Generic test coach #4 for QA and development.',
        'experience_years': 10,
        'certifications': 'Test Certification D',
        'coach_bio': 'Test coach bio for coach #4.',
        'specialization_notes': 'Yoga and mobility',
        'specializations': ['Yoga & Flexibility'],
        'pricing': [('1-on-1 Session', 55.00), ('Group Class', 18.00)],
    },
    {
        'email': 'coach5@test.fit',
        'first_name': 'Test',
        'last_name': 'CoachFive',
        'phone': '+1-555-1005',
        'bio': 'Generic test coach #5 for QA and development.',
        'experience_years': 4,
        'certifications': 'Test Certification E',
        'coach_bio': 'Test coach bio for coach #5.',
        'specialization_notes': 'Muscle building',
        'specializations': ['Muscle Gain'],
        'pricing': [('1-on-1 Session', 65.00), ('Monthly Package', 250.00)],
    },
]

TEST_CLIENTS = [
    {
        'email': 'client1@test.fit',
        'first_name': 'Test',
        'last_name': 'ClientOne',
        'phone': '+1-555-2001',
        'bio': 'Generic test client #1 for QA and development.',
    },
    {
        'email': 'client2@test.fit',
        'first_name': 'Test',
        'last_name': 'ClientTwo',
        'phone': '+1-555-2002',
        'bio': 'Generic test client #2 for QA and development.',
    },
    {
        'email': 'client3@test.fit',
        'first_name': 'Test',
        'last_name': 'ClientThree',
        'phone': '+1-555-2003',
        'bio': 'Generic test client #3 for QA and development.',
    },
    {
        'email': 'client4@test.fit',
        'first_name': 'Test',
        'last_name': 'ClientFour',
        'phone': '+1-555-2004',
        'bio': 'Generic test client #4 for QA and development.',
    },
    {
        'email': 'client5@test.fit',
        'first_name': 'Test',
        'last_name': 'ClientFive',
        'phone': '+1-555-2005',
        'bio': 'Generic test client #5 for QA and development.',
    },
]


def get_or_create_specialization(name):
    spec = Specialization.query.filter_by(name=name).first()
    if not spec:
        spec = Specialization(name=name, category='fitness')
        db.session.add(spec)
        db.session.flush()
    return spec


def create_admin(data):
    if User.query.filter_by(email=data['email']).first():
        return False

    user = User(email=data['email'], role='admin', status='active')
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.flush()

    db.session.add(UserProfile(
        user_id=user.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
    ))
    db.session.commit()
    return True


def create_coach(data):
    if User.query.filter_by(email=data['email']).first():
        return False

    user = User(email=data['email'], role='coach', status='active')
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.flush()

    db.session.add(UserProfile(
        user_id=user.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        bio=data['bio'],
        phone=data['phone'],
    ))

    db.session.add(CoachSurvey(
        user_id=user.id,
        experience_years=data['experience_years'],
        certifications=data['certifications'],
        bio=data['coach_bio'],
        specialization_notes=data['specialization_notes'],
    ))

    for spec_name in data['specializations']:
        spec = get_or_create_specialization(spec_name)
        db.session.add(CoachSpecialization(
            coach_id=user.id,
            specialization_id=spec.id,
        ))

    for session_type, price in data['pricing']:
        db.session.add(CoachPricing(
            coach_id=user.id,
            session_type=session_type,
            price=price,
            currency='USD',
        ))

    db.session.commit()
    return True


def create_client(data):
    if User.query.filter_by(email=data['email']).first():
        return False

    user = User(email=data['email'], role='client', status='active')
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.flush()

    db.session.add(UserProfile(
        user_id=user.id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        bio=data.get('bio'),
        phone=data.get('phone'),
    ))
    db.session.commit()
    return True


def main():
    print("=" * 60)
    print("Creating test accounts")
    print("=" * 60)
    print(f"Shared password: {PASSWORD}\n")

    # Admin
    print("Admin:")
    if create_admin(ADMIN_ACCOUNT):
        print(f"  + created {ADMIN_ACCOUNT['email']}")
    else:
        print(f"  - {ADMIN_ACCOUNT['email']} already exists, skipped")

    # Coaches
    print("\nCoaches:")
    for data in TEST_COACHES:
        if create_coach(data):
            print(f"  + created {data['email']}")
        else:
            print(f"  - {data['email']} already exists, skipped")

    # Clients
    print("\nClients:")
    for data in TEST_CLIENTS:
        if create_client(data):
            print(f"  + created {data['email']}")
        else:
            print(f"  - {data['email']} already exists, skipped")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    print(f"\nAll test accounts use password: {PASSWORD}")
    print("\nAccounts:")
    print(f"  Admin:   {ADMIN_ACCOUNT['email']}")
    print(f"  Coaches: coach1@test.fit ... coach5@test.fit")
    print(f"  Clients: client1@test.fit ... client5@test.fit")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        main()
