"""
Seed sample workout plans with days, exercises, logs, and calendar notes.
Run after seed_demo_data.py and seed_workout_library.py.
"""

from app import create_app
from models import (
    db,
    WorkoutPlan,
    WorkoutDay,
    PlanExercise,
    WorkoutLog,
    CalendarNote,
    Exercise,
    User,
)
from datetime import datetime, date, timedelta

app = create_app()

with app.app_context():
    print("Seeding sample workout data...")

    # Get some exercises
    exercises = {e.name: e for e in Exercise.query.all()}

    # Get some clients
    clients = {
        u.id: u for u in User.query.filter(User.role.in_(("client", "both"))).all()
    }
    client_ids = list(clients.keys())

    # Get some coaches
    coaches = {
        u.id: u for u in User.query.filter(User.role.in_(("coach", "both"))).all()
    }
    coach_ids = list(coaches.keys())

    if not client_ids or not coach_ids:
        print("Need at least one client and one coach. Run seed_demo_data.py first.")
        exit(1)

    today = date.today()

    # ---- Plan 1: Beginner Full Body (4 weeks, 3 days/week) ----
    print("Creating: Beginner Full Body Plan")
    p1 = WorkoutPlan(
        name="Beginner Full Body",
        description="A 4-week full body program for beginners. 3 days per week focusing on compound movements.",
        coach_id=coach_ids[0],
        client_id=client_ids[0],
        start_date=today - timedelta(days=14),
        end_date=today + timedelta(days=14),
        status="active",
    )
    db.session.add(p1)
    db.session.flush()

    days_p1 = [
        (
            "Day 1: Full Body A",
            1,
            [
                ("Barbell Squat", 3, "10", "bodyweight", 90),
                ("Bench Press", 3, "10", "bodyweight", 90),
                ("Pull-ups", 3, "8", "bodyweight", 90),
            ],
        ),
        (
            "Day 2: Full Body B",
            2,
            [
                ("Deadlift", 3, "8", "bodyweight", 120),
                ("Push-ups", 3, "15", "bodyweight", 60),
                ("Lunges", 3, "12", "bodyweight", 60),
            ],
        ),
        (
            "Day 3: Full Body C",
            3,
            [
                ("Barbell Squat", 3, "10", "bodyweight", 90),
                ("Dumbbell Shoulder Press", 3, "10", "bodyweight", 90),
                ("Plank", 3, "60", "bodyweight", 60),
            ],
        ),
    ]
    for day_name, day_num, ex_list in days_p1:
        day = WorkoutDay(plan_id=p1.id, name=day_name, day_number=day_num)
        db.session.add(day)
        db.session.flush()
        for ex_name, sets, reps, weight, rest in ex_list:
            ex = exercises.get(ex_name)
            if ex:
                db.session.add(
                    PlanExercise(
                        workout_day_id=day.id,
                        exercise_id=ex.id,
                        sets=sets,
                        reps=reps,
                        weight=weight,
                        rest_seconds=rest,
                    )
                )

    # ---- Plan 2: Intermediate Strength (6 weeks, 4 days/week) ----
    print("Creating: Intermediate Strength Plan")
    p2 = WorkoutPlan(
        name="Intermediate Strength",
        description="6-week strength program. Upper/lower split, 4 days per week.",
        coach_id=coach_ids[0] if len(coach_ids) > 0 else coach_ids[0],
        client_id=client_ids[1] if len(client_ids) > 1 else client_ids[0],
        start_date=today - timedelta(days=7),
        end_date=today + timedelta(days=35),
        status="active",
    )
    db.session.add(p2)
    db.session.flush()

    days_p2 = [
        (
            "Day 1: Upper Push",
            1,
            [
                ("Bench Press", 4, "8", "135lbs", 120),
                ("Dumbbell Shoulder Press", 3, "10", "40lbs", 90),
                ("Push-ups", 3, "15", "bodyweight", 60),
            ],
        ),
        (
            "Day 2: Lower",
            2,
            [
                ("Barbell Squat", 4, "8", "185lbs", 120),
                ("Deadlift", 3, "6", "225lbs", 180),
                ("Lunges", 3, "12", "bodyweight", 60),
            ],
        ),
        (
            "Day 3: Upper Pull",
            3,
            [
                ("Pull-ups", 4, "8", "bodyweight", 120),
                ("Bench Press", 3, "10", "135lbs", 90),
                ("Plank", 3, "60", "bodyweight", 60),
            ],
        ),
        (
            "Day 4: Lower + Core",
            4,
            [
                ("Barbell Squat", 3, "10", "155lbs", 90),
                ("Deadlift", 3, "8", "205lbs", 120),
                ("Plank", 3, "60", "bodyweight", 60),
            ],
        ),
    ]
    for day_name, day_num, ex_list in days_p2:
        day = WorkoutDay(plan_id=p2.id, name=day_name, day_number=day_num)
        db.session.add(day)
        db.session.flush()
        for ex_name, sets, reps, weight, rest in ex_list:
            ex = exercises.get(ex_name)
            if ex:
                db.session.add(
                    PlanExercise(
                        workout_day_id=day.id,
                        exercise_id=ex.id,
                        sets=sets,
                        reps=reps,
                        weight=weight,
                        rest_seconds=rest,
                    )
                )

    # ---- Plan 3: Yoga Flexibility (4 weeks, daily) ----
    print("Creating: Yoga Flexibility Plan")
    p3 = WorkoutPlan(
        name="Yoga Flexibility",
        description="4-week yoga program for flexibility and stress relief. Daily sessions.",
        coach_id=coach_ids[0],
        client_id=client_ids[0],
        start_date=today,
        end_date=today + timedelta(days=28),
        status="active",
    )
    db.session.add(p3)
    db.session.flush()

    days_p3 = [
        (
            "Day 1: Morning Flow",
            1,
            [
                ("Downward Dog", 1, "5", "bodyweight", 0),
                ("Cat-Cow Stretch", 1, "10", "bodyweight", 0),
                ("Pigeon Pose", 1, "5", "bodyweight", 0),
            ],
        ),
        (
            "Day 2: Hip Openers",
            2,
            [
                ("Pigeon Pose", 1, "5", "bodyweight", 0),
                ("Hamstring Stretch", 1, "5", "bodyweight", 0),
                ("Tree Pose", 1, "5", "bodyweight", 0),
            ],
        ),
        (
            "Day 3: Upper Body Stretch",
            3,
            [
                ("Cat-Cow Stretch", 1, "10", "bodyweight", 0),
                ("Shoulder Circles", 1, "10", "bodyweight", 0),
                ("Downward Dog", 1, "5", "bodyweight", 0),
            ],
        ),
    ]
    for day_name, day_num, ex_list in days_p3:
        day = WorkoutDay(plan_id=p3.id, name=day_name, day_number=day_num)
        db.session.add(day)
        db.session.flush()
        for ex_name, sets, reps, weight, rest in ex_list:
            ex = exercises.get(ex_name)
            if ex:
                db.session.add(
                    PlanExercise(
                        workout_day_id=day.id,
                        exercise_id=ex.id,
                        sets=sets,
                        reps=reps,
                        weight=weight,
                        rest_seconds=rest,
                    )
                )

    # ---- Workout Logs (completed sessions for the past 2 weeks) ----
    print("Creating workout logs...")
    log_entries = [
        (
            client_ids[0],
            today - timedelta(days=1),
            "Push Day A",
            45,
            4,
            "Felt strong today",
        ),
        (
            client_ids[0],
            today - timedelta(days=3),
            "Full Body B",
            50,
            5,
            "Great session",
        ),
        (client_ids[0], today - timedelta(days=5), "Yoga Flow", 30, 4, "Very relaxing"),
        (
            client_ids[0],
            today - timedelta(days=7),
            "Push Day A",
            45,
            3,
            "Tired but pushed through",
        ),
        (
            client_ids[0],
            today - timedelta(days=10),
            "Full Body B",
            55,
            5,
            "New PR on squats!",
        ),
        (client_ids[0], today - timedelta(days=12), "Yoga Flow", 30, 4, "Nice stretch"),
    ]
    if len(client_ids) > 1:
        log_entries.extend(
            [
                (
                    client_ids[1],
                    today - timedelta(days=1),
                    "Upper Push",
                    60,
                    4,
                    "Good pump",
                ),
                (
                    client_ids[1],
                    today - timedelta(days=2),
                    "Lower Day",
                    55,
                    5,
                    "Legs are dead",
                ),
                (
                    client_ids[1],
                    today - timedelta(days=4),
                    "Upper Pull",
                    50,
                    4,
                    "Pull-ups getting easier",
                ),
            ]
        )

    for cid, log_date, name, duration, rating, notes in log_entries:
        db.session.add(
            WorkoutLog(
                client_id=cid,
                date=log_date,
                workout_name=name,
                duration_minutes=duration,
                rating=rating,
                notes=notes,
                completed=True,
            )
        )

    # ---- Calendar Notes ----
    print("Creating calendar notes...")
    note_entries = [
        (client_ids[0], today, "Rest day - focus on recovery and hydration"),
        (
            client_ids[0],
            today + timedelta(days=1),
            "Leg day tomorrow - eat extra carbs tonight",
        ),
        (client_ids[0], today + timedelta(days=3), "Yoga class at 6pm"),
        (client_ids[0], today - timedelta(days=2), "Felt great during today's session"),
    ]
    if len(client_ids) > 1:
        note_entries.extend(
            [
                (client_ids[1], today, "Upper body day - warm up shoulders"),
                (
                    client_ids[1],
                    today + timedelta(days=2),
                    "Lower body - don't skip warmup",
                ),
            ]
        )

    for uid, note_date, note in note_entries:
        db.session.add(CalendarNote(user_id=uid, date=note_date, note=note))

    db.session.commit()

    # Summary
    plans = WorkoutPlan.query.count()
    days = WorkoutDay.query.count()
    plan_ex = PlanExercise.query.count()
    logs = WorkoutLog.query.count()
    notes = CalendarNote.query.count()

    print(f"\n{'=' * 50}")
    print("Sample data seeded successfully!")
    print(f"{'=' * 50}")
    print(f"  Workout plans: {plans}")
    print(f"  Workout days: {days}")
    print(f"  Plan exercises: {plan_ex}")
    print(f"  Workout logs: {logs}")
    print(f"  Calendar notes: {notes}")
