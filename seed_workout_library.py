"""
Seed the workout library with a handful of placeholder workouts.

Each entry represents a complete workout activity (not a single movement),
with estimated calories, default duration, category, and target muscle group.

Run this AFTER migrate_workout_library.py:
    python seed_workout_library.py
"""
from app import create_app
from models import db, Exercise

app = create_app()

# (name, description, category, muscle_group, equipment, difficulty,
#  calories, default_duration_minutes, instructions)
LIBRARY_WORKOUTS = [
    (
        "Morning Jog",
        "Easy outdoor jog at a conversational pace to build aerobic base.",
        "cardio",
        "legs",
        "none",
        "beginner",
        280,
        30,
        "Warm up with 5 minutes of brisk walking, then jog at a steady, comfortable pace.",
    ),
    (
        "HIIT Cardio Blast",
        "High-intensity interval training alternating all-out effort and rest.",
        "cardio",
        "full-body",
        "bodyweight",
        "advanced",
        350,
        20,
        "30 seconds max-effort, 30 seconds rest. Repeat for 20 minutes.",
    ),
    (
        "Indoor Cycling",
        "Steady-state stationary bike ride with moderate resistance.",
        "cardio",
        "legs",
        "stationary bike",
        "beginner",
        300,
        45,
        "Maintain cadence of 80-90 RPM at moderate resistance.",
    ),
    (
        "Upper Body Strength",
        "Classic push/pull routine focused on the chest, back, and arms.",
        "strength",
        "upper-body",
        "dumbbells",
        "intermediate",
        220,
        40,
        "3 sets of: bench press, rows, shoulder press, curls, tricep extensions.",
    ),
    (
        "Leg Day",
        "Compound lower-body strength session targeting quads, hamstrings, and glutes.",
        "strength",
        "legs",
        "barbell",
        "intermediate",
        320,
        50,
        "Squats, Romanian deadlifts, lunges, and calf raises. 4 sets each.",
    ),
    (
        "Core Crusher",
        "Focused abdominal and core stability circuit.",
        "strength",
        "core",
        "bodyweight",
        "beginner",
        150,
        20,
        "Plank, mountain climbers, bicycle crunches, leg raises. 3 rounds.",
    ),
    (
        "Full-Body Bodyweight",
        "No-equipment circuit hitting every major muscle group.",
        "strength",
        "full-body",
        "bodyweight",
        "beginner",
        260,
        30,
        "Push-ups, squats, lunges, plank, burpees. 4 rounds.",
    ),
    (
        "Vinyasa Yoga Flow",
        "Dynamic yoga sequence for flexibility and mobility.",
        "flexibility",
        "full-body",
        "yoga mat",
        "beginner",
        180,
        45,
        "Flow through sun salutations, warrior poses, and deep stretches.",
    ),
    (
        "Mobility & Stretch",
        "Slow-paced mobility routine to release tension and improve range of motion.",
        "flexibility",
        "full-body",
        "yoga mat",
        "beginner",
        90,
        20,
        "Hip openers, hamstring stretches, shoulder circles, cat-cow.",
    ),
    (
        "Balance Training",
        "Balance and stability drills for improved coordination.",
        "balance",
        "legs",
        "none",
        "beginner",
        110,
        20,
        "Single-leg stands, heel-to-toe walks, tree pose. Hold each for 30 seconds.",
    ),
    (
        "Pickup Basketball",
        "Casual basketball game — sprint, jump, pivot, and shoot.",
        "sports",
        "full-body",
        "basketball",
        "intermediate",
        500,
        60,
        "Play a full-court pickup game with friends at a moderate pace.",
    ),
    (
        "Pool Swim",
        "Freestyle lap swimming for low-impact full-body cardio.",
        "cardio",
        "full-body",
        "pool",
        "intermediate",
        400,
        40,
        "Warm up 200m easy, then 20 x 50m with 15s rest.",
    ),
]


with app.app_context():
    print("Seeding workout library...")

    created = 0
    updated = 0
    for (
        name,
        desc,
        category,
        muscle,
        equipment,
        difficulty,
        calories,
        duration,
        instructions,
    ) in LIBRARY_WORKOUTS:
        existing = Exercise.query.filter_by(name=name).first()
        if existing:
            # Upgrade an existing matching row into a library workout
            existing.description = desc
            existing.category = category
            existing.muscle_group = muscle
            existing.equipment = equipment
            existing.difficulty = difficulty
            existing.calories = calories
            existing.default_duration_minutes = duration
            existing.instructions = instructions
            existing.is_library_workout = True
            existing.is_public = True
            updated += 1
        else:
            exercise = Exercise(
                name=name,
                description=desc,
                category=category,
                muscle_group=muscle,
                equipment=equipment,
                difficulty=difficulty,
                instructions=instructions,
                calories=calories,
                default_duration_minutes=duration,
                is_library_workout=True,
                is_public=True,
            )
            db.session.add(exercise)
            created += 1

    db.session.commit()

    total = Exercise.query.filter_by(is_library_workout=True).count()
    print(f"✓ Created {created}, updated {updated}")
    print(f"✓ Workout library now contains {total} workouts")
