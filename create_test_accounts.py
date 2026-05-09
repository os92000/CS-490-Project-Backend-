"""
Create one paired client and coach account with varied historical data.
Usage:
    python create_test_accounts.py

What this script seeds:
- 1 client account and 1 coach account
- Accepted hire request and active coach relationship
- Coach profile data (survey, specializations, pricing, availability)
- Fitness survey for the client
- Workout plans, plan metadata, days, plan exercises, assignments
- Workout logs and exercise logs with varied intensity and cadence
- Meal logs with calories, protein, carbs, fat
- Daily metrics, body metrics, wellness logs, meal plans
- Chat messages, reviews, notifications, payment records

Date range:
- Starts: 2025-01-01
- Ends:   2026-05-09

Re-running is safe: old dummy records for these emails are removed first.
"""

from datetime import date, datetime, time, timedelta
import json
import math
import random
from sqlalchemy import MetaData, Table, inspect, text

from app import create_app
from models import (
    db,
    BodyMetric,
    ChatMessage,
    ClientRequest,
    CoachAvailability,
    CoachPricing,
    CoachRelationship,
    CoachSpecialization,
    CoachSurvey,
    DailyMetric,
    Exercise,
    ExerciseLog,
    FitnessSurvey,
    MealLog,
    MealPlan,
    Notification,
    PaymentRecord,
    PlanExercise,
    Review,
    Specialization,
    User,
    UserProfile,
    WellnessLog,
    WorkoutDay,
    WorkoutLog,
    WorkoutPlan,
    WorkoutPlanAssignment,
    WorkoutPlanMetadata,
)

CLIENT_EMAIL = "client.john@fitapp.local"
COACH_EMAIL = "coach.jane@fitapp.local"
PASSWORD = "FitData2026!"
SEED = 49026

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 5, 9)
HISTORY_DAYS = (END_DATE - START_DATE).days + 1

def _daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def _ensure_specializations():
    specs = [
        ("Strength Training", "fitness"),
        ("Weight Loss", "fitness"),
        ("Cardio Training", "fitness"),
        ("Nutrition Coaching", "nutrition"),
    ]

    for name, category in specs:
        if not Specialization.query.filter_by(name=name).first():
            db.session.add(Specialization(name=name, category=category))
    db.session.commit()


def _ensure_exercises():
    fallback_exercises = [
        ("Barbell Squat", "strength", "legs", "barbell", "intermediate", 170, 40),
        ("Bench Press", "strength", "chest", "barbell", "intermediate", 160, 35),
        ("Deadlift", "strength", "back", "barbell", "advanced", 220, 35),
        ("Push-up", "strength", "chest", "bodyweight", "beginner", 110, 20),
        ("Pull-up", "strength", "back", "pull-up bar", "intermediate", 140, 20),
        ("Dumbbell Row", "strength", "back", "dumbbells", "beginner", 130, 25),
        ("Lunge", "strength", "legs", "bodyweight", "beginner", 120, 25),
        ("Plank", "strength", "core", "bodyweight", "beginner", 90, 12),
        ("Running", "cardio", "full-body", "none", "beginner", 320, 30),
        ("Cycling", "cardio", "legs", "bike", "beginner", 300, 35),
        ("Jump Rope", "cardio", "full-body", "jump rope", "intermediate", 280, 20),
        ("Rowing", "cardio", "full-body", "rowing machine", "intermediate", 290, 25),
        ("Yoga Flow", "flexibility", "full-body", "yoga mat", "beginner", 140, 30),
        ("Mobility Circuit", "flexibility", "full-body", "none", "beginner", 110, 20),
        ("Single-Leg Balance", "balance", "legs", "none", "beginner", 80, 15),
        ("Pick-up Basketball", "sports", "full-body", "ball", "intermediate", 360, 45),
    ]

    for name, category, muscle, equipment, difficulty, calories, duration in fallback_exercises:
        if Exercise.query.filter_by(name=name).first():
            continue

        db.session.add(
            Exercise(
                name=name,
                description=f"Dummy seeded exercise: {name}",
                category=category,
                muscle_group=muscle,
                equipment=equipment,
                difficulty=difficulty,
                instructions=f"Maintain clean form for {name} and progress gradually.",
                is_public=True,
                is_library_workout=True,
                calories=calories,
                default_duration_minutes=duration,
            )
        )

    db.session.commit()


def _clear_existing_accounts(client_email, coach_email):
    client_user = User.query.filter_by(email=client_email).first()
    coach_user = User.query.filter_by(email=coach_email).first()

    user_ids = [u.id for u in (client_user, coach_user) if u]
    if not user_ids:
        return

    relationship_ids = [
        r.id
        for r in CoachRelationship.query.filter(
            db.or_(
                CoachRelationship.client_id.in_(user_ids),
                CoachRelationship.coach_id.in_(user_ids),
            )
        ).all()
    ]

    plan_ids = [
        p.id
        for p in WorkoutPlan.query.filter(
            db.or_(WorkoutPlan.client_id.in_(user_ids), WorkoutPlan.coach_id.in_(user_ids))
        ).all()
    ]

    day_ids = []
    if plan_ids:
        day_ids = [d.id for d in WorkoutDay.query.filter(WorkoutDay.plan_id.in_(plan_ids)).all()]

    log_ids = [l.id for l in WorkoutLog.query.filter(WorkoutLog.client_id.in_(user_ids)).all()]

    if relationship_ids:
        ChatMessage.query.filter(ChatMessage.relationship_id.in_(relationship_ids)).delete(synchronize_session=False)

    ClientRequest.query.filter(
        db.or_(ClientRequest.client_id.in_(user_ids), ClientRequest.coach_id.in_(user_ids))
    ).delete(synchronize_session=False)

    Review.query.filter(
        db.or_(Review.client_id.in_(user_ids), Review.coach_id.in_(user_ids))
    ).delete(synchronize_session=False)

    if log_ids:
        ExerciseLog.query.filter(ExerciseLog.workout_log_id.in_(log_ids)).delete(synchronize_session=False)

    WorkoutLog.query.filter(WorkoutLog.client_id.in_(user_ids)).delete(synchronize_session=False)

    if day_ids:
        PlanExercise.query.filter(PlanExercise.workout_day_id.in_(day_ids)).delete(synchronize_session=False)

    if plan_ids:
        WorkoutPlanAssignment.query.filter(WorkoutPlanAssignment.plan_id.in_(plan_ids)).delete(
            synchronize_session=False
        )
        WorkoutPlanMetadata.query.filter(WorkoutPlanMetadata.plan_id.in_(plan_ids)).delete(
            synchronize_session=False
        )
        WorkoutDay.query.filter(WorkoutDay.plan_id.in_(plan_ids)).delete(synchronize_session=False)
        WorkoutPlan.query.filter(WorkoutPlan.id.in_(plan_ids)).delete(synchronize_session=False)

    WorkoutPlanAssignment.query.filter(WorkoutPlanAssignment.user_id.in_(user_ids)).delete(
        synchronize_session=False
    )

    MealLog.query.filter(MealLog.user_id.in_(user_ids)).delete(synchronize_session=False)
    BodyMetric.query.filter(BodyMetric.user_id.in_(user_ids)).delete(synchronize_session=False)
    WellnessLog.query.filter(WellnessLog.user_id.in_(user_ids)).delete(synchronize_session=False)
    DailyMetric.query.filter(DailyMetric.user_id.in_(user_ids)).delete(synchronize_session=False)
    MealPlan.query.filter(MealPlan.user_id.in_(user_ids)).delete(synchronize_session=False)
    FitnessSurvey.query.filter(FitnessSurvey.user_id.in_(user_ids)).delete(synchronize_session=False)
    Notification.query.filter(Notification.user_id.in_(user_ids)).delete(synchronize_session=False)

    PaymentRecord.query.filter(
        db.or_(PaymentRecord.payer_id.in_(user_ids), PaymentRecord.coach_id.in_(user_ids))
    ).delete(synchronize_session=False)

    CoachAvailability.query.filter(CoachAvailability.coach_id.in_(user_ids)).delete(synchronize_session=False)
    CoachPricing.query.filter(CoachPricing.coach_id.in_(user_ids)).delete(synchronize_session=False)
    CoachSpecialization.query.filter(CoachSpecialization.coach_id.in_(user_ids)).delete(synchronize_session=False)
    CoachSurvey.query.filter(CoachSurvey.user_id.in_(user_ids)).delete(synchronize_session=False)

    if relationship_ids:
        CoachRelationship.query.filter(CoachRelationship.id.in_(relationship_ids)).delete(synchronize_session=False)

    UserProfile.query.filter(UserProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
    User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)

    db.session.commit()


def _create_users_and_relationship(rng):
    coach = User(email=COACH_EMAIL, role="coach", status="active")
    coach.set_password(PASSWORD)
    db.session.add(coach)
    db.session.flush()

    client = User(email=CLIENT_EMAIL, role="client", status="active")
    client.set_password(PASSWORD)
    db.session.add(client)
    db.session.flush()

    db.session.add(
        UserProfile(
            user_id=coach.id,
            first_name="Jane",
            last_name="Doe",
            phone="+1-556-490-1001",
            bio="Coach profile for analytics, UI validation, and relationship testing.",
        )
    )

    db.session.add(
        UserProfile(
            user_id=client.id,
            first_name="John",
            last_name="Smith",
            phone="+1-556-490-2001",
            bio="Client profile with long varied data history.",
        )
    )

    db.session.add(
        CoachSurvey(
            user_id=coach.id,
            experience_years=8,
            certifications="NASM-CPT, Precision Nutrition L1",
            bio="Structured coach focused on practical plans and consistency.",
            specialization_notes="Strength progression, body recomposition, nutrition habits.",
        )
    )

    spec_names = ["Strength Training", "Weight Loss", "Nutrition Coaching", "Cardio Training"]
    for spec_name in spec_names:
        spec = Specialization.query.filter_by(name=spec_name).first()
        if spec:
            db.session.add(CoachSpecialization(coach_id=coach.id, specialization_id=spec.id))

    db.session.add_all(
        [
            CoachPricing(coach_id=coach.id, session_type="1-on-1 Session", price=89.00, currency="USD"),
            CoachPricing(coach_id=coach.id, session_type="Monthly Package", price=299.00, currency="USD"),
            CoachPricing(coach_id=coach.id, session_type="Nutrition Check-in", price=49.00, currency="USD"),
        ]
    )

    for day_of_week in [0, 1, 2, 3, 4]:
        db.session.add(
            CoachAvailability(
                coach_id=coach.id,
                day_of_week=day_of_week,
                start_time=time(8, 0),
                end_time=time(18, 0),
            )
        )

    request_date = datetime.combine(START_DATE + timedelta(days=5), time(10, 30))
    accepted_date = request_date + timedelta(days=1)
    db.session.add(
        ClientRequest(
            client_id=client.id,
            coach_id=coach.id,
            status="accepted",
            requested_at=request_date,
            responded_at=accepted_date,
        )
    )

    relationship = CoachRelationship(
        client_id=client.id,
        coach_id=coach.id,
        status="active",
        start_date=datetime.combine(START_DATE + timedelta(days=8), time(9, 0)),
    )
    db.session.add(relationship)

    db.session.add(
        FitnessSurvey(
            user_id=client.id,
            weight=98.4,
            age=31,
            fitness_level="intermediate",
            goals="Lose fat, improve strength, and sustain consistency with better nutrition.",
            completed_at=datetime.combine(START_DATE + timedelta(days=10), time(11, 15)),
        )
    )

    db.session.commit()
    return client, coach, relationship


def _build_plan_windows():
    return [
        (START_DATE + timedelta(days=0), START_DATE + timedelta(days=98), "completed"),
        (START_DATE + timedelta(days=120), START_DATE + timedelta(days=224), "completed"),
        (START_DATE + timedelta(days=245), START_DATE + timedelta(days=350), "completed"),
        (END_DATE - timedelta(days=84), END_DATE + timedelta(days=35), "active"),
    ]


def _create_plans_and_logs(client, coach, rng):
    exercises = Exercise.query.order_by(Exercise.id.asc()).all()
    if len(exercises) < 8:
        raise RuntimeError("Need at least 8 exercises to generate dummy plans and logs")

    workout_log_count = 0
    exercise_log_count = 0

    for idx, (start, end, status) in enumerate(_build_plan_windows(), start=1):
        plan = WorkoutPlan(
            name=f"Dummy Progress Block {idx}",
            description="Auto-seeded plan for chart and filter validation.",
            coach_id=coach.id,
            client_id=client.id,
            start_date=start,
            end_date=end,
            status=status,
        )
        db.session.add(plan)
        db.session.flush()

        db.session.add(
            WorkoutPlanMetadata(
                plan_id=plan.id,
                goal="Recomposition and work capacity",
                difficulty="intermediate" if idx < 4 else "advanced",
                plan_type="hybrid",
                duration_weeks=max(6, (end - start).days // 7),
            )
        )

        day_templates = [
            ("Day 1: Lower + Core", ["legs", "core"]),
            ("Day 2: Upper Strength", ["chest", "back", "shoulders"]),
            ("Day 3: Conditioning", ["full-body", "legs"]),
        ]

        plan_days = []
        for day_num, (day_name, muscles) in enumerate(day_templates, start=1):
            day = WorkoutDay(
                plan_id=plan.id,
                name=day_name,
                day_number=day_num,
                notes="Progressive overload with controlled fatigue.",
            )
            db.session.add(day)
            db.session.flush()
            plan_days.append(day)

            candidates = [
                ex for ex in exercises
                if (ex.muscle_group in muscles) or (ex.category in ["cardio", "strength"])
            ]
            if len(candidates) < 3:
                candidates = exercises

            for order, ex in enumerate(rng.sample(candidates, 3), start=1):
                db.session.add(
                    PlanExercise(
                        workout_day_id=day.id,
                        exercise_id=ex.id,
                        order=order,
                        sets=4 if ex.category == "strength" else 1,
                        reps="6-10" if ex.category == "strength" else None,
                        duration_minutes=18 if ex.category == "cardio" else None,
                        rest_seconds=90 if ex.category == "strength" else 45,
                        weight="progressive" if ex.category == "strength" else "bodyweight",
                        notes="Track effort and keep reps clean.",
                    )
                )

        assigned_cursor = start
        while assigned_cursor <= min(end, END_DATE):
            if assigned_cursor.weekday() in [0, 2, 4]:
                day_map = {0: plan_days[0], 2: plan_days[1], 4: plan_days[2]}
                db.session.add(
                    WorkoutPlanAssignment(
                        user_id=client.id,
                        plan_id=plan.id,
                        workout_day_id=day_map[assigned_cursor.weekday()].id,
                        assigned_date=assigned_cursor,
                    )
                )
            assigned_cursor += timedelta(days=1)

        log_cursor = start
        while log_cursor <= min(end, END_DATE):
            day_map = {0: plan_days[0], 2: plan_days[1], 4: plan_days[2]}
            if log_cursor.weekday() not in day_map:
                log_cursor += timedelta(days=1)
                continue

            # Compliance changes over time so filter windows show visible shifts.
            days_from_start = (log_cursor - START_DATE).days
            phase = days_from_start / max(HISTORY_DAYS - 1, 1)
            base_compliance = 0.58 + (phase * 0.30)
            if log_cursor > END_DATE - timedelta(days=30):
                base_compliance += 0.08
            do_log = rng.random() < min(base_compliance, 0.95)

            if do_log:
                day = day_map[log_cursor.weekday()]
                day_exercises = PlanExercise.query.filter_by(workout_day_id=day.id).order_by(PlanExercise.order.asc()).all()
                lead_ex = day_exercises[0].exercise if day_exercises else None

                # Duration and rating trend upward with periodic dips.
                trend_minutes = 38 + int(22 * phase)
                wave_minutes = int(8 * math.sin(days_from_start / 18.0))
                duration = max(25, trend_minutes + wave_minutes + rng.randint(-7, 9))

                base_rating = 2.8 + (1.5 * phase) + (0.35 * math.sin(days_from_start / 30.0))
                rating = int(round(max(1, min(5, base_rating + rng.uniform(-0.7, 0.7)))))

                calories_burned = max(180, int(duration * (5.5 + rng.uniform(-1.0, 1.2))))

                log = WorkoutLog(
                    client_id=client.id,
                    plan_id=plan.id,
                    workout_day_id=day.id,
                    library_exercise_id=lead_ex.id if lead_ex else None,
                    workout_name=day.name,
                    calories_burned=calories_burned,
                    exercise_type=lead_ex.category if lead_ex else "strength",
                    muscle_group=lead_ex.muscle_group if lead_ex else "full-body",
                    date=log_cursor,
                    duration_minutes=duration,
                    notes="Session complete. Tracking effort and progression.",
                    rating=rating,
                    completed=True,
                )
                db.session.add(log)
                db.session.flush()
                workout_log_count += 1

                for pe in day_exercises:
                    ex = pe.exercise
                    if ex and ex.category == "strength":
                        sets = 4
                        reps = ",".join(str(rng.randint(6, 11)) for _ in range(sets))
                        weight_used = f"{rng.randint(30, 110)}kg"
                        duration_minutes = None
                    else:
                        sets = 1
                        reps = None
                        weight_used = "bodyweight"
                        duration_minutes = rng.randint(12, 28)

                    db.session.add(
                        ExerciseLog(
                            workout_log_id=log.id,
                            exercise_id=pe.exercise_id,
                            sets_completed=sets,
                            reps_completed=reps,
                            weight_used=weight_used,
                            duration_minutes=duration_minutes,
                            notes="Solid form and controlled pace.",
                        )
                    )
                    exercise_log_count += 1

            # Occasional ad-hoc cardio session.
            if rng.random() < 0.12:
                cardio_pool = [e for e in exercises if e.category in ["cardio", "sports"]]
                if cardio_pool:
                    ex = cardio_pool[rng.randrange(len(cardio_pool))]
                    duration = rng.randint(20, 55)
                    db.session.add(
                        WorkoutLog(
                            client_id=client.id,
                            plan_id=None,
                            workout_day_id=None,
                            library_exercise_id=ex.id,
                            workout_name=ex.name,
                            calories_burned=max(150, int(duration * (6.5 + rng.uniform(-1.2, 1.2)))),
                            exercise_type=ex.category,
                            muscle_group=ex.muscle_group,
                            date=log_cursor,
                            duration_minutes=duration,
                            notes="Extra standalone cardio session.",
                            rating=rng.randint(2, 5),
                            completed=True,
                        )
                    )
                    workout_log_count += 1

            log_cursor += timedelta(days=1)

        db.session.commit()

    return workout_log_count, exercise_log_count


def _daily_macro_targets(days_from_start):
    phase = days_from_start / max(HISTORY_DAYS - 1, 1)

    # Intake becomes more consistent and slightly lower through time.
    seasonal = math.sin(days_from_start / 27.0)
    calories = int(2620 - (320 * phase) + (190 * seasonal))
    protein = int(135 + (45 * phase) + (12 * math.sin(days_from_start / 40.0)))
    carbs = int(330 - (75 * phase) + (30 * math.sin(days_from_start / 17.0)))
    fat = int(88 - (18 * phase) + (10 * math.sin(days_from_start / 23.0)))

    return {
        "calories": max(1650, calories),
        "protein": max(90, protein),
        "carbs": max(140, carbs),
        "fat": max(45, fat),
    }


def _create_nutrition_and_wellness(client, rng):
    meal_count = 0
    daily_metric_count = 0
    wellness_count = 0
    body_metric_count = 0

    metadata = MetaData()
    daily_metrics_table = Table("daily_metrics", metadata, autoload_with=db.engine)
    daily_metric_cols = set(daily_metrics_table.c.keys())
    daily_metric_date_col = "log_date" if "log_date" in daily_metric_cols else "date"

    meal_templates = {
        "breakfast": [
            "Greek yogurt, berries, oats",
            "Egg scramble with toast and fruit",
            "Protein smoothie with banana and peanut butter",
            "Overnight oats with whey and chia",
        ],
        "lunch": [
            "Chicken rice bowl with vegetables",
            "Turkey wrap with side salad",
            "Salmon quinoa plate",
            "Beef and potato meal prep bowl",
        ],
        "dinner": [
            "Lean beef stir fry with rice",
            "Grilled chicken, sweet potato, greens",
            "Tofu curry with jasmine rice",
            "Shrimp pasta with mixed vegetables",
        ],
        "snack": [
            "Protein bar and apple",
            "Cottage cheese with fruit",
            "Almonds and banana",
            "Rice cakes with peanut butter",
        ],
    }

    # Meal logs for the most recent ~13 months so nutrition filters are rich but bounded.
    nutrition_start = END_DATE - timedelta(days=400)

    for day in _daterange(nutrition_start, END_DATE):
        days_from_start = (day - START_DATE).days
        weekday = day.weekday()
        targets = _daily_macro_targets(days_from_start)

        # Weekends tend to be a bit higher in calories.
        if weekday in [5, 6]:
            targets["calories"] += 120
            targets["carbs"] += 20

        meals_today = ["breakfast", "lunch", "dinner"]
        if rng.random() < 0.68:
            meals_today.append("snack")

        split = {
            "breakfast": 0.24,
            "lunch": 0.31,
            "dinner": 0.35,
            "snack": 0.10,
        }

        for meal_type in meals_today:
            cal = int(targets["calories"] * split[meal_type] + rng.randint(-70, 90))
            pro = round(max(8, targets["protein"] * split[meal_type] + rng.uniform(-4, 5)), 2)
            carb = round(max(8, targets["carbs"] * split[meal_type] + rng.uniform(-8, 9)), 2)
            fat = round(max(4, targets["fat"] * split[meal_type] + rng.uniform(-3, 3)), 2)

            db.session.add(
                MealLog(
                    user_id=client.id,
                    date=day,
                    meal_type=meal_type,
                    food_items=meal_templates[meal_type][rng.randrange(len(meal_templates[meal_type]))],
                    calories=max(90, cal),
                    protein_g=pro,
                    carbs_g=carb,
                    fat_g=fat,
                    notes="Dummy nutrition entry with realistic macro variation.",
                )
            )
            meal_count += 1

    # Daily metrics and wellness across full range.
    for idx, day in enumerate(_daterange(START_DATE, END_DATE)):
        phase = idx / max(HISTORY_DAYS - 1, 1)

        steps = int(6400 + 2500 * phase + 1700 * math.sin(idx / 21.0) + rng.randint(-1300, 1500))
        calories_burned = int(1850 + 300 * phase + 180 * math.sin(idx / 19.0) + rng.randint(-180, 220))
        water_ml = int(1900 + 520 * phase + 230 * math.sin(idx / 16.0) + rng.randint(-260, 320))

        daily_metric_row = {
            "user_id": client.id,
            "steps": max(2800, steps),
            "calories_burned": max(1450, calories_burned),
            "water_intake_ml": max(1100, water_ml),
            "notes": "Dummy daily activity marker.",
            "created_at": datetime.utcnow(),
            daily_metric_date_col: day,
        }
        db.session.execute(daily_metrics_table.insert().values(**daily_metric_row))
        daily_metric_count += 1

        # Wellness 6 days a week to keep data dense but not perfectly complete.
        if day.weekday() != 6 or rng.random() < 0.45:
            sleep_hours = round(6.5 + 0.9 * phase + 0.45 * math.sin(idx / 25.0) + rng.uniform(-0.7, 0.8), 2)
            energy = int(5.2 + 2.8 * phase + rng.uniform(-1.2, 1.3))
            stress = int(6.2 - 2.1 * phase + rng.uniform(-1.4, 1.4))

            if sleep_hours >= 8.0:
                sleep_quality = "excellent"
                mood = "excellent"
            elif sleep_hours >= 7.0:
                sleep_quality = "good"
                mood = "good"
            elif sleep_hours >= 6.0:
                sleep_quality = "fair"
                mood = "okay"
            else:
                sleep_quality = "poor"
                mood = "poor"

            if rng.random() < 0.05:
                mood = "terrible"

            db.session.add(
                WellnessLog(
                    user_id=client.id,
                    date=day,
                    mood=mood,
                    energy_level=max(1, min(10, energy)),
                    stress_level=max(1, min(10, stress)),
                    sleep_hours=max(4.2, min(9.4, sleep_hours)),
                    sleep_quality=sleep_quality,
                    water_intake_ml=max(1100, water_ml),
                    notes="Dummy wellness check-in.",
                )
            )
            wellness_count += 1

        # Body metrics once per week.
        if day.weekday() == 0:
            weight = round(99.2 - 12.4 * phase + 0.8 * math.sin(idx / 33.0) + rng.uniform(-0.5, 0.45), 2)
            body_fat = round(30.6 - 6.8 * phase + rng.uniform(-0.3, 0.3), 2)

            db.session.add(
                BodyMetric(
                    user_id=client.id,
                    date=day,
                    weight_kg=max(81.0, weight),
                    body_fat_percentage=max(17.5, body_fat),
                    muscle_mass_kg=round(34.8 + 3.9 * phase + rng.uniform(-0.25, 0.3), 2),
                    chest_cm=round(109.0 - 3.2 * phase + rng.uniform(-0.25, 0.2), 2),
                    waist_cm=round(101.5 - 13.5 * phase + rng.uniform(-0.5, 0.55), 2),
                    hips_cm=round(107.2 - 5.0 * phase + rng.uniform(-0.3, 0.35), 2),
                    arms_cm=round(33.8 + 2.0 * phase + rng.uniform(-0.15, 0.2), 2),
                    thighs_cm=round(62.4 - 2.1 * phase + rng.uniform(-0.2, 0.2), 2),
                    notes="Dummy weekly body metric check-in.",
                )
            )
            body_metric_count += 1

    # Personal meal plan notes users can edit in-app.
    plan_titles = [
        "High Protein Weekday Plan",
        "Office Lunch Rotation",
        "Travel Day Fallback Plan",
        "Maintenance Calories Plan",
        "Low Prep Busy Week Plan",
    ]

    meal_plan_columns = {column["name"] for column in inspect(db.engine).get_columns("meal_plans")}
    meal_plan_title_column = "name" if "name" in meal_plan_columns else "title" if "title" in meal_plan_columns else None
    if meal_plan_title_column is None:
        raise RuntimeError("meal_plans table is missing both 'name' and 'title' columns")

    for title in plan_titles:
        values = {
            "user_id": client.id,
            meal_plan_title_column: title,
            "notes": "Dummy meal plan notes with options and substitutions.",
            "created_at": datetime.utcnow(),
        }
        columns_sql = ", ".join(values.keys())
        placeholders_sql = ", ".join(f":{key}" for key in values)
        db.session.execute(
            text(f"INSERT INTO meal_plans ({columns_sql}) VALUES ({placeholders_sql})"),
            values,
        )

    db.session.commit()

    return {
        "meal_logs": meal_count,
        "daily_metrics": daily_metric_count,
        "wellness_logs": wellness_count,
        "body_metrics": body_metric_count,
        "meal_plans": len(plan_titles),
    }


def _create_social_and_payment_data(client, coach, relationship, rng):
    end_dt = datetime.combine(END_DATE, time(18, 0))
    start_dt = datetime.combine(START_DATE, time(9, 0))

    chat_count = 0
    weeks = max(1, HISTORY_DAYS // 7)
    for week in range(weeks):
        for msg_idx in range(2):
            sent_at = start_dt + timedelta(days=(week * 7) + (msg_idx * 2), hours=rng.randint(0, 8))
            if sent_at > end_dt:
                continue

            sender_id = client.id if msg_idx == 0 else coach.id
            if sender_id == client.id:
                text = f"Weekly check-in {week + 1}: workouts logged, nutrition mostly on target, energy improving."
            else:
                text = f"Coach reply {week + 1}: keep consistency, adjust load gradually, and prioritize sleep this week."

            db.session.add(
                ChatMessage(
                    relationship_id=relationship.id,
                    sender_id=sender_id,
                    message=text,
                    sent_at=sent_at,
                    read_at=sent_at + timedelta(minutes=rng.randint(10, 180)),
                )
            )
            chat_count += 1

    review_payloads = [
        (5, "Great coaching support and clear progress structure."),
        (5, "Very responsive coach with practical plan adjustments."),
        (4, "Strong guidance and realistic recommendations for busy weeks."),
    ]

    review_count = 0
    for idx, (rating, comment) in enumerate(review_payloads):
        db.session.add(
            Review(
                client_id=client.id,
                coach_id=coach.id,
                rating=rating,
                comment=comment,
                created_at=end_dt - timedelta(days=90 * (idx + 1)),
            )
        )
        review_count += 1

    notification_count = 0
    for i in range(70):
        created_at = end_dt - timedelta(days=i * 7)
        if created_at < start_dt:
            break

        milestone = i % 4 == 0
        db.session.add(
            Notification(
                user_id=client.id,
                type="milestone" if milestone else "system",
                title="Milestone unlocked" if milestone else "Weekly summary ready",
                message=(
                    "You hit a consistency milestone this week."
                    if milestone
                    else "Your weekly analytics summary is available."
                ),
                read=i > 4,
                created_at=created_at,
            )
        )
        notification_count += 1

    payment_count = 0
    for i in range(18):
        created_at = end_dt - timedelta(days=i * 28 + 3)
        if created_at < start_dt:
            break

        amount = 299.00 if i % 3 != 0 else 89.00
        metadata = {
            "package": "Monthly Package" if amount > 100 else "Single Session",
            "seed_tag": "dummy_account",
            "index": i,
        }

        db.session.add(
            PaymentRecord(
                payer_id=client.id,
                coach_id=coach.id,
                payment_reference=f"dummy-{client.id}-{i:03d}",
                amount=amount,
                currency="USD",
                status="completed",
                metadata_json=json.dumps(metadata),
                created_at=created_at,
            )
        )
        payment_count += 1

    db.session.commit()

    return {
        "chat_messages": chat_count,
        "reviews": review_count,
        "notifications": notification_count,
        "payments": payment_count,
    }


def main():
    rng = random.Random(SEED)

    print("=" * 72)
    print("Seeding paired coach-client data")
    print("=" * 72)
    print(f"Range: {START_DATE.isoformat()} to {END_DATE.isoformat()}")

    _ensure_specializations()
    _ensure_exercises()
    _clear_existing_accounts(CLIENT_EMAIL, COACH_EMAIL)

    client, coach, relationship = _create_users_and_relationship(rng)
    workout_logs, exercise_logs = _create_plans_and_logs(client, coach, rng)
    nutrition_counts = _create_nutrition_and_wellness(client, rng)
    social_counts = _create_social_and_payment_data(client, coach, relationship, rng)

    print("\nAccounts")
    print(f"  Client:   {CLIENT_EMAIL}")
    print(f"  Coach:    {COACH_EMAIL}")
    print(f"  Password: {PASSWORD}")

    print("\nSeed summary")
    print(f"  Workout logs: {workout_logs}")
    print(f"  Exercise logs: {exercise_logs}")
    print(f"  Meal logs: {nutrition_counts['meal_logs']}")
    print(f"  Daily metrics: {nutrition_counts['daily_metrics']}")
    print(f"  Wellness logs: {nutrition_counts['wellness_logs']}")
    print(f"  Body metrics: {nutrition_counts['body_metrics']}")
    print(f"  Meal plans: {nutrition_counts['meal_plans']}")
    print(f"  Chat messages: {social_counts['chat_messages']}")
    print(f"  Reviews: {social_counts['reviews']}")
    print(f"  Notifications: {social_counts['notifications']}")
    print(f"  Payments: {social_counts['payments']}")
    print("=" * 72)


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        main()
