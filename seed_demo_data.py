"""
Seed demo data for fitness app
Run this script to populate the database with demo coaches, exercises, and reviews
"""
from app import create_app
from models import db, User, UserProfile, Specialization, CoachSurvey, CoachSpecialization, CoachPricing, Exercise, Review, WorkoutPlan, WorkoutDay, PlanExercise
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("Starting to seed demo data...")

    # Clear existing demo data (optional)
    # Specialization.query.delete()
    # db.session.commit()

    # 1. Create Specializations
    specializations_data = [
        ('Weight Loss', 'fitness'),
        ('Muscle Gain', 'fitness'),
        ('Cardio Training', 'fitness'),
        ('Strength Training', 'fitness'),
        ('Yoga & Flexibility', 'wellness'),
        ('Sports Performance', 'athletic'),
        ('Senior Fitness', 'specialized'),
        ('Injury Recovery', 'rehabilitation'),
        ('Nutrition Coaching', 'nutrition'),
        ('CrossFit', 'fitness')
    ]

    specializations = []
    for name, category in specializations_data:
        existing = Specialization.query.filter_by(name=name).first()
        if not existing:
            spec = Specialization(name=name, category=category)
            db.session.add(spec)
            specializations.append(spec)
        else:
            specializations.append(existing)

    db.session.commit()
    print(f"✓ Created {len(specializations)} specializations")

    # 2. Create Demo Coaches
    coaches_data = [
        {
            'email': 'sarah.johnson@demo.fit',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'bio': 'Certified personal trainer with 8+ years of experience specializing in weight loss transformation. Helped over 200 clients achieve their fitness goals through personalized programs.',
            'phone': '+1-555-0101',
            'experience_years': 8,
            'certifications': 'ACE Certified Personal Trainer, Nutrition Specialist',
            'coach_bio': 'Expert in creating sustainable weight loss programs that focus on lifestyle changes rather than quick fixes.',
            'specialization_notes': 'Weight loss, nutrition planning, habit building',
            'specializations': ['Weight Loss', 'Nutrition Coaching'],
            'pricing': [
                ('1-on-1 Session', 75.00),
                ('Monthly Package', 250.00),
                ('Group Session', 35.00)
            ]
        },
        {
            'email': 'marcus.rodriguez@demo.fit',
            'first_name': 'Marcus',
            'last_name': 'Rodriguez',
            'bio': 'Former competitive powerlifter and strength coach. Passionate about helping people build strength and confidence through progressive training programs.',
            'phone': '+1-555-0102',
            'experience_years': 10,
            'certifications': 'NSCA-CSCS, USA Powerlifting Coach',
            'coach_bio': 'Specialized in strength training, powerlifting, and muscle building with proven track record.',
            'specialization_notes': 'Strength training, powerlifting, muscle building',
            'specializations': ['Muscle Gain', 'Strength Training'],
            'pricing': [
                ('1-on-1 Session', 85.00),
                ('Monthly Package', 300.00)
            ]
        },
        {
            'email': 'emily.chen@demo.fit',
            'first_name': 'Emily',
            'last_name': 'Chen',
            'bio': 'Certified yoga instructor and wellness coach focusing on mind-body connection. Specializes in flexibility, stress reduction, and holistic health.',
            'phone': '+1-555-0103',
            'experience_years': 6,
            'certifications': 'RYT-500, Wellness Coach Certification',
            'coach_bio': 'Creating balanced fitness programs that integrate yoga, meditation, and functional movement.',
            'specialization_notes': 'Yoga, flexibility, mindfulness',
            'specializations': ['Yoga & Flexibility'],
            'pricing': [
                ('1-on-1 Session', 65.00),
                ('Monthly Package', 220.00),
                ('Group Class', 25.00)
            ]
        },
        {
            'email': 'david.thompson@demo.fit',
            'first_name': 'David',
            'last_name': 'Thompson',
            'bio': 'Sports performance coach working with athletes from high school to professional level. Expert in speed, agility, and sport-specific conditioning.',
            'phone': '+1-555-0104',
            'experience_years': 12,
            'certifications': 'CSCS, USAW Sports Performance Coach',
            'coach_bio': 'Former collegiate athlete now helping others reach peak performance in their sport.',
            'specialization_notes': 'Sports performance, speed training, agility',
            'specializations': ['Sports Performance', 'Strength Training'],
            'pricing': [
                ('1-on-1 Session', 95.00),
                ('Monthly Package', 350.00)
            ]
        },
        {
            'email': 'lisa.martinez@demo.fit',
            'first_name': 'Lisa',
            'last_name': 'Martinez',
            'bio': 'Specialized in senior fitness and functional training. Focused on improving mobility, balance, and quality of life for older adults.',
            'phone': '+1-555-0105',
            'experience_years': 7,
            'certifications': 'Senior Fitness Specialist, ACE Certified',
            'coach_bio': 'Compassionate approach to helping seniors maintain independence through fitness.',
            'specialization_notes': 'Senior fitness, balance, mobility',
            'specializations': ['Senior Fitness', 'Injury Recovery'],
            'pricing': [
                ('1-on-1 Session', 70.00),
                ('Monthly Package', 240.00)
            ]
        }
    ]

    demo_coaches = []
    for coach_data in coaches_data:
        # Check if coach already exists
        existing = User.query.filter_by(email=coach_data['email']).first()
        if existing:
            print(f"  Coach {coach_data['email']} already exists, skipping...")
            demo_coaches.append(existing)
            continue

        # Create user
        user = User(email=coach_data['email'], role='coach', status='active')
        user.set_password('Demo123!')
        db.session.add(user)
        db.session.flush()

        # Create profile
        profile = UserProfile(
            user_id=user.id,
            first_name=coach_data['first_name'],
            last_name=coach_data['last_name'],
            bio=coach_data['bio'],
            phone=coach_data['phone']
        )
        db.session.add(profile)

        # Create coach survey
        coach_survey = CoachSurvey(
            user_id=user.id,
            experience_years=coach_data['experience_years'],
            certifications=coach_data['certifications'],
            bio=coach_data['coach_bio'],
            specialization_notes=coach_data['specialization_notes']
        )
        db.session.add(coach_survey)

        # Add specializations
        for spec_name in coach_data['specializations']:
            spec = Specialization.query.filter_by(name=spec_name).first()
            if spec:
                coach_spec = CoachSpecialization(coach_id=user.id, specialization_id=spec.id)
                db.session.add(coach_spec)

        # Add pricing
        for session_type, price in coach_data['pricing']:
            pricing = CoachPricing(
                coach_id=user.id,
                session_type=session_type,
                price=price,
                currency='USD'
            )
            db.session.add(pricing)

        demo_coaches.append(user)
        db.session.commit()
        print(f"  ✓ Created coach: {coach_data['first_name']} {coach_data['last_name']}")

    print(f"✓ Total coaches created/verified: {len(demo_coaches)}")

    # 3. Add Reviews
    if len(demo_coaches) >= 4:
        reviews_data = [
            (0, 5, 'Sarah helped me lose 30 pounds in 4 months! Her approach is sustainable and she really cares about her clients.', 30),
            (0, 5, 'Best coach I have ever worked with. Very knowledgeable and supportive throughout my journey.', 60),
            (0, 4, 'Great coach! Very professional and creates personalized plans. Would recommend.', 90),
            (1, 5, 'Marcus knows his stuff! Increased my deadlift by 100lbs in 6 months. Excellent programming.', 45),
            (1, 5, 'If you want to get strong, Marcus is your guy. No nonsense approach that gets results.', 20),
            (2, 5, 'Emily is amazing! My flexibility has improved so much and I feel less stressed. Highly recommend!', 15),
            (2, 4, 'Very calming and knowledgeable instructor. Great for beginners and advanced students.', 40),
            (3, 5, 'Helped improve my vertical jump and sprint speed significantly. Great for athletes!', 25),
        ]

        for coach_idx, rating, comment, days_ago in reviews_data:
            if coach_idx < len(demo_coaches):
                review = Review(
                    client_id=demo_coaches[coach_idx].id,
                    coach_id=demo_coaches[coach_idx].id,
                    rating=rating,
                    comment=comment,
                    created_at=datetime.utcnow() - timedelta(days=days_ago)
                )
                db.session.add(review)

        db.session.commit()
        print(f"✓ Created {len(reviews_data)} reviews")

    # 4. Create Exercise Database
    exercises_data = [
        # Cardio
        ('Running', '30 minutes of steady-state running', 'cardio', 'full-body', 'none', 'beginner', 'Maintain steady pace for entire duration'),
        ('Jump Rope', 'High-intensity jump rope intervals', 'cardio', 'full-body', 'jump rope', 'intermediate', 'Jump for 30 seconds, rest 30 seconds, repeat'),
        ('Cycling', 'Stationary or outdoor cycling', 'cardio', 'legs', 'bike', 'beginner', 'Maintain moderate resistance and steady cadence'),
        ('Rowing Machine', 'Full body cardio workout', 'cardio', 'full-body', 'rowing machine', 'intermediate', 'Focus on proper form: legs, core, arms'),
        ('Burpees', 'Full body explosive movement', 'cardio', 'full-body', 'bodyweight', 'advanced', 'Squat, plank, push-up, jump. Repeat continuously'),

        # Strength
        ('Barbell Squat', 'Compound lower body exercise', 'strength', 'legs', 'barbell', 'intermediate', 'Keep chest up, squat to parallel or below, drive through heels'),
        ('Bench Press', 'Upper body pushing exercise', 'strength', 'chest', 'barbell', 'intermediate', 'Lower bar to chest, press up explosively, keep elbows at 45 degrees'),
        ('Deadlift', 'Posterior chain compound movement', 'strength', 'back', 'barbell', 'advanced', 'Hip hinge movement, keep back neutral, drive through floor'),
        ('Pull-ups', 'Bodyweight back exercise', 'strength', 'back', 'pull-up bar', 'intermediate', 'Pull chin over bar, control descent, full extension at bottom'),
        ('Push-ups', 'Upper body bodyweight exercise', 'strength', 'chest', 'bodyweight', 'beginner', 'Keep body straight, lower chest to ground, push back up'),
        ('Dumbbell Shoulder Press', 'Shoulder strength exercise', 'strength', 'shoulders', 'dumbbells', 'beginner', 'Press dumbbells overhead, control descent, maintain core stability'),
        ('Lunges', 'Single leg lower body exercise', 'strength', 'legs', 'bodyweight', 'beginner', 'Step forward, lower back knee to ground, drive back to start'),
        ('Plank', 'Core stability exercise', 'strength', 'core', 'bodyweight', 'beginner', 'Hold straight body position on forearms, engage core and glutes'),

        # Flexibility
        ('Hamstring Stretch', 'Lower body flexibility', 'flexibility', 'legs', 'none', 'beginner', 'Reach toward toes, hold for 30 seconds, breathe deeply'),
        ('Cat-Cow Stretch', 'Spine mobility exercise', 'flexibility', 'back', 'none', 'beginner', 'Alternate between arching and rounding spine, sync with breath'),
        ('Shoulder Circles', 'Upper body mobility', 'flexibility', 'shoulders', 'none', 'beginner', 'Make large circles with arms, both directions'),
        ('Downward Dog', 'Full body yoga pose', 'flexibility', 'full-body', 'yoga mat', 'beginner', 'Form inverted V with body, press heels down, relax shoulders'),
        ('Pigeon Pose', 'Hip flexibility yoga pose', 'flexibility', 'hips', 'yoga mat', 'intermediate', 'Bring knee forward, extend back leg, fold forward over front leg'),

        # Balance
        ('Single Leg Stand', 'Basic balance exercise', 'balance', 'legs', 'none', 'beginner', 'Stand on one leg for 30 seconds, switch legs'),
        ('Tree Pose', 'Yoga balance pose', 'balance', 'legs', 'yoga mat', 'beginner', 'Place foot on inner thigh, hands in prayer position, focus on single point'),
    ]

    for name, desc, category, muscle, equipment, difficulty, instructions in exercises_data:
        existing = Exercise.query.filter_by(name=name).first()
        if not existing:
            exercise = Exercise(
                name=name,
                description=desc,
                category=category,
                muscle_group=muscle,
                equipment=equipment,
                difficulty=difficulty,
                instructions=instructions,
                is_public=True
            )
            db.session.add(exercise)

    db.session.commit()
    print(f"✓ Created exercise database with 20 exercises")

    print("\n" + "="*50)
    print("Demo data seeded successfully!")
    print("="*50)
    print("\nDemo Coach Accounts (Password: Demo123!):")
    for coach in demo_coaches[:5]:
        profile = UserProfile.query.filter_by(user_id=coach.id).first()
        if profile:
            print(f"  • {profile.first_name} {profile.last_name}: {coach.email}")

    print("\nYou can now browse coaches and see demo content!")
    print("Users can still add new coaches, exercises, and other data.")
