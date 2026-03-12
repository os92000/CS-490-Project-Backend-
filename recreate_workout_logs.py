"""
Migration script to recreate workout_logs table to match the WorkoutLog model
Run this with: python recreate_workout_logs.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting workout_logs table recreation...")

    try:
        # Step 1: Check existing data
        print("1. Checking existing workout_logs...")
        result = db.session.execute(text("SELECT COUNT(*) as count FROM workout_logs"))
        count = result.fetchone()[0]
        print(f"   Found {count} existing workout logs")

        if count > 0:
            print("\n2. Creating final backup...")
            db.session.execute(text("DROP TABLE IF EXISTS workout_logs_old_backup"))
            db.session.execute(text("""
                CREATE TABLE workout_logs_old_backup AS
                SELECT * FROM workout_logs
            """))
            db.session.commit()
            print(f"   ✓ Backed up {count} logs to workout_logs_old_backup")

        # Step 2: Disable foreign key checks
        print("\n3. Disabling foreign key checks...")
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.commit()
        print("   ✓ Foreign key checks disabled")

        # Step 3: Drop the old table
        print("\n4. Dropping old workout_logs table...")
        db.session.execute(text("DROP TABLE IF EXISTS workout_logs"))
        db.session.commit()
        print("   ✓ Dropped old table")

        # Step 4: Create new table with correct structure
        print("\n5. Creating new workout_logs table...")
        db.session.execute(text("""
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
        """))
        db.session.commit()
        print("   ✓ Created new table with correct schema")

        # Step 5: Re-enable foreign key checks
        print("\n6. Re-enabling foreign key checks...")
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        print("   ✓ Foreign key checks enabled")

        # Step 6: Show new structure
        print("\n7. New table structure:")
        result = db.session.execute(text("DESCRIBE workout_logs"))
        for row in result.fetchall():
            print(f"   {row[0]}: {row[1]}")

        print("\n" + "="*60)
        print("Recreation completed successfully!")
        print("="*60)
        print(f"Old data backed up to: workout_logs_old_backup ({count} records)")
        print("New workout_logs table ready for use")
        print("\nNote: Old exercise-level logs are in workout_logs_old_backup")
        print("New table is for workout session-level logs")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
