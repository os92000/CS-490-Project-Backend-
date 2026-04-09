"""
Combined migration script for all backend schema changes.

Runs every migration step in dependency order, detecting current DB state
and skipping any step that has already been applied. Safe to re-run.

Run this with: python migrate_all.py

Steps applied (in order):
  1. exercises: add category, video_url, is_public, created_at (rename
     legacy 'approved' -> 'is_public' if present)
  2. workout_plans: recreate if on the pre-Phase-2 legacy schema
     (single user_id / goal / difficulty / type columns)
  3. workout_logs: recreate if on the pre-Phase-2 legacy per-exercise schema
     (no client_id / workout_day_id columns)
  4. Add workout library fields:
       exercises.calories, exercises.default_duration_minutes,
       exercises.is_library_workout, workout_logs.library_exercise_id,
       workout_logs.workout_name, workout_logs.calories_burned,
       workout_logs.exercise_type, workout_logs.muscle_group,
       plus FK fk_workout_logs_library_exercise
  5. workout_plans.coach_id: make nullable so clients can create self-plans

Backups created during destructive steps:
  - workout_plans_backup       (if step 2 runs)
  - workout_logs_old_backup    (if step 3 runs)
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()


# ============================================================================
# Helpers
# ============================================================================

def _table_exists(connection, table):
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = :table
            """
        ),
        {"table": table},
    )
    return result.scalar() > 0


def _column_exists(connection, table, column):
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    )
    return result.scalar() > 0


def _foreign_key_exists(connection, table, constraint):
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) FROM information_schema.table_constraints
            WHERE table_schema = DATABASE()
              AND table_name = :table
              AND constraint_name = :constraint
              AND constraint_type = 'FOREIGN KEY'
            """
        ),
        {"table": table, "constraint": constraint},
    )
    return result.scalar() > 0


def _column_is_nullable(connection, table, column):
    result = connection.execute(
        text(
            """
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    )
    row = result.fetchone()
    return row is not None and row[0] == 'YES'


def _count_rows(connection, table):
    result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
    return result.scalar() or 0


# ============================================================================
# Step 1: exercises schema cleanup
# ============================================================================

def step_fix_exercises_schema(connection):
    """Ensure exercises table has category, video_url, is_public, created_at."""
    if not _table_exists(connection, 'exercises'):
        return "exercises table does not exist yet; skipping"

    changes = []

    if not _column_exists(connection, 'exercises', 'category'):
        connection.execute(text(
            "ALTER TABLE exercises ADD COLUMN category "
            "ENUM('cardio', 'strength', 'flexibility', 'balance', 'sports') "
            "AFTER description"
        ))
        changes.append("added category")

    if not _column_exists(connection, 'exercises', 'video_url'):
        connection.execute(text(
            "ALTER TABLE exercises ADD COLUMN video_url VARCHAR(255) AFTER difficulty"
        ))
        changes.append("added video_url")

    has_approved = _column_exists(connection, 'exercises', 'approved')
    has_is_public = _column_exists(connection, 'exercises', 'is_public')
    if has_approved and not has_is_public:
        connection.execute(text(
            "ALTER TABLE exercises ADD COLUMN is_public BOOLEAN DEFAULT TRUE AFTER created_by"
        ))
        connection.execute(text("UPDATE exercises SET is_public = approved"))
        connection.execute(text("ALTER TABLE exercises DROP COLUMN approved"))
        changes.append("renamed approved -> is_public")
    elif not has_is_public:
        connection.execute(text(
            "ALTER TABLE exercises ADD COLUMN is_public BOOLEAN DEFAULT TRUE AFTER created_by"
        ))
        changes.append("added is_public")

    if not _column_exists(connection, 'exercises', 'created_at'):
        connection.execute(text(
            "ALTER TABLE exercises ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ))
        changes.append("added created_at")

    return ", ".join(changes) if changes else None


# ============================================================================
# Step 2: workout_plans legacy recreation
# ============================================================================

def step_recreate_workout_plans_if_legacy(connection):
    """
    Legacy workout_plans used `user_id` / `goal` / `difficulty` / `type`.
    New schema uses `coach_id` / `client_id`. Skip if already on new schema.
    """
    if not _table_exists(connection, 'workout_plans'):
        return "workout_plans table does not exist yet; skipping"

    if _column_exists(connection, 'workout_plans', 'coach_id'):
        return None  # already on new schema

    print("   - Legacy workout_plans schema detected, recreating...")

    backup_count = _count_rows(connection, 'workout_plans')
    connection.execute(text("DROP TABLE IF EXISTS workout_plans_backup"))
    connection.execute(text(
        "CREATE TABLE workout_plans_backup AS SELECT * FROM workout_plans"
    ))
    print(f"   - Backed up {backup_count} rows to workout_plans_backup")

    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    connection.execute(text("DROP TABLE IF EXISTS workout_plans"))
    # Create with the modern schema including nullable coach_id from step 5
    connection.execute(text(
        """
        CREATE TABLE workout_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            coach_id INT NULL,
            client_id INT NOT NULL,
            start_date DATE,
            end_date DATE,
            status ENUM('active', 'completed', 'archived') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ))

    # Restore workout_days FK if it was dropped by the old-table drop
    if _table_exists(connection, 'workout_days') and not _foreign_key_exists(
        connection, 'workout_days', 'workout_days_ibfk_1'
    ):
        connection.execute(text(
            """
            ALTER TABLE workout_days
            ADD CONSTRAINT workout_days_ibfk_1
            FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
            """
        ))

    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    # Best-effort data migration: legacy user_id becomes self-created client plan
    if backup_count > 0:
        connection.execute(text(
            """
            INSERT INTO workout_plans (name, description, coach_id, client_id, start_date, status, created_at)
            SELECT
                name,
                CONCAT_WS(' | ',
                    IFNULL(CONCAT('Goal: ', goal), ''),
                    IFNULL(CONCAT('Difficulty: ', difficulty), ''),
                    IFNULL(CONCAT('Type: ', type), '')
                ) as description,
                NULL as coach_id,
                user_id as client_id,
                DATE(created_at) as start_date,
                'active' as status,
                created_at
            FROM workout_plans_backup
            WHERE user_id IS NOT NULL
            """
        ))

    return f"recreated with new schema, migrated {backup_count} legacy row(s)"


# ============================================================================
# Step 3: workout_logs legacy recreation
# ============================================================================

def step_recreate_workout_logs_if_legacy(connection):
    """
    Legacy workout_logs was per-exercise. New schema is session-level with
    client_id, plan_id, workout_day_id, date, etc. Skip if already on new schema.
    """
    if not _table_exists(connection, 'workout_logs'):
        return "workout_logs table does not exist yet; skipping"

    if (
        _column_exists(connection, 'workout_logs', 'client_id')
        and _column_exists(connection, 'workout_logs', 'workout_day_id')
    ):
        return None  # already on new schema

    print("   - Legacy workout_logs schema detected, recreating...")

    backup_count = _count_rows(connection, 'workout_logs')
    connection.execute(text("DROP TABLE IF EXISTS workout_logs_old_backup"))
    connection.execute(text(
        "CREATE TABLE workout_logs_old_backup AS SELECT * FROM workout_logs"
    ))
    print(f"   - Backed up {backup_count} rows to workout_logs_old_backup")

    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    connection.execute(text("DROP TABLE IF EXISTS workout_logs"))
    connection.execute(text(
        """
        CREATE TABLE workout_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT NOT NULL,
            plan_id INT,
            workout_day_id INT,
            date DATE NOT NULL,
            duration_minutes INT,
            notes TEXT,
            rating INT,
            completed BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE SET NULL,
            FOREIGN KEY (workout_day_id) REFERENCES workout_days(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ))
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    return f"recreated with new schema, backup has {backup_count} row(s)"


# ============================================================================
# Step 4: workout library fields
# ============================================================================

def step_add_workout_library_fields(connection):
    """Add library-related columns to exercises and workout_logs."""
    if not _table_exists(connection, 'exercises') or not _table_exists(connection, 'workout_logs'):
        return "prerequisite tables missing; skipping"

    changes = []

    exercise_columns = [
        ("calories", "INT NULL"),
        ("default_duration_minutes", "INT NULL"),
        ("is_library_workout", "TINYINT(1) NOT NULL DEFAULT 0"),
    ]
    for col, ddl in exercise_columns:
        if not _column_exists(connection, 'exercises', col):
            connection.execute(text(f"ALTER TABLE exercises ADD COLUMN {col} {ddl}"))
            changes.append(f"exercises.{col}")

    log_columns = [
        ("library_exercise_id", "INT NULL"),
        ("workout_name", "VARCHAR(200) NULL"),
        ("calories_burned", "INT NULL"),
        ("exercise_type", "VARCHAR(50) NULL"),
        ("muscle_group", "VARCHAR(100) NULL"),
    ]
    for col, ddl in log_columns:
        if not _column_exists(connection, 'workout_logs', col):
            connection.execute(text(f"ALTER TABLE workout_logs ADD COLUMN {col} {ddl}"))
            changes.append(f"workout_logs.{col}")

    # FK constraint for library_exercise_id
    fk_name = 'fk_workout_logs_library_exercise'
    if (
        _column_exists(connection, 'workout_logs', 'library_exercise_id')
        and not _foreign_key_exists(connection, 'workout_logs', fk_name)
    ):
        connection.execute(text(
            f"""
            ALTER TABLE workout_logs
            ADD CONSTRAINT {fk_name}
            FOREIGN KEY (library_exercise_id)
            REFERENCES exercises(id)
            ON DELETE SET NULL
            """
        ))
        changes.append(f"FK {fk_name}")

    return ", ".join(changes) if changes else None


# ============================================================================
# Step 5: workout_plans.coach_id nullable
# ============================================================================

def step_make_coach_id_nullable(connection):
    """Make workout_plans.coach_id nullable so clients can create self-plans."""
    if not _table_exists(connection, 'workout_plans'):
        return "workout_plans table does not exist yet; skipping"

    if not _column_exists(connection, 'workout_plans', 'coach_id'):
        return "coach_id column missing; skipping"

    if _column_is_nullable(connection, 'workout_plans', 'coach_id'):
        return None

    connection.execute(text(
        "ALTER TABLE workout_plans MODIFY COLUMN coach_id INT NULL"
    ))
    return "coach_id is now nullable"


# ============================================================================
# Runner
# ============================================================================

STEPS = [
    ("1. Fix exercises schema", step_fix_exercises_schema),
    ("2. Recreate workout_plans (if legacy)", step_recreate_workout_plans_if_legacy),
    ("3. Recreate workout_logs (if legacy)", step_recreate_workout_logs_if_legacy),
    ("4. Add workout library fields", step_add_workout_library_fields),
    ("5. Make workout_plans.coach_id nullable", step_make_coach_id_nullable),
]


def main():
    print("=" * 70)
    print("Running combined migration")
    print("=" * 70)

    with app.app_context():
        connection = db.session.connection()
        try:
            for name, fn in STEPS:
                print(f"\n{name}")
                result = fn(connection)
                if result is None:
                    print("   - already up to date")
                else:
                    print(f"   - {result}")
            db.session.commit()
            print("\n" + "=" * 70)
            print("All migrations completed successfully!")
            print("=" * 70)
        except Exception as e:
            db.session.rollback()
            print(f"\nMigration failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    main()
