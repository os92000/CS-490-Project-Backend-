"""
Migration script to fix workout_plans table structure
Run this with: python migrate_workout_schema.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting workout_plans schema migration...")

    try:
        # Step 1: Create backup table
        print("1. Creating backup of existing data...")
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS workout_plans_backup AS
            SELECT * FROM workout_plans
        """))
        db.session.commit()

        # Get count of backed up plans
        result = db.session.execute(text("SELECT COUNT(*) as count FROM workout_plans_backup"))
        backup_count = result.fetchone()[0]
        print(f"   ✓ Backed up {backup_count} workout plans")

        # Step 2: Drop foreign key constraints
        print("2. Dropping foreign key constraints...")

        # Disable foreign key checks temporarily
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.session.commit()
        print("   ✓ Disabled foreign key checks")

        # Step 3: Drop and recreate table
        print("3. Recreating workout_plans table with correct structure...")
        db.session.execute(text("DROP TABLE IF EXISTS workout_plans"))
        db.session.commit()

        db.session.execute(text("""
            CREATE TABLE workout_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                coach_id INT NOT NULL,
                client_id INT,
                start_date DATE,
                end_date DATE,
                status ENUM('draft', 'active', 'completed', 'archived') DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.session.commit()
        print("   ✓ Table recreated with correct schema")

        # Step 4: Restore foreign key on workout_days
        print("4. Restoring foreign key constraints...")
        db.session.execute(text("""
            ALTER TABLE workout_days
            ADD CONSTRAINT workout_days_ibfk_1
            FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE
        """))
        db.session.commit()

        # Re-enable foreign key checks
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.session.commit()
        print("   ✓ Foreign key constraints restored")

        # Step 5: Migrate data from backup
        print("5. Migrating data from backup...")
        if backup_count > 0:
            db.session.execute(text("""
                INSERT INTO workout_plans (name, description, coach_id, client_id, start_date, status, created_at)
                SELECT
                    name,
                    CONCAT_WS(' | ',
                        IFNULL(CONCAT('Goal: ', goal), ''),
                        IFNULL(CONCAT('Difficulty: ', difficulty), ''),
                        IFNULL(CONCAT('Type: ', type), '')
                    ) as description,
                    user_id as coach_id,
                    NULL as client_id,
                    DATE(created_at) as start_date,
                    'active' as status,
                    created_at
                FROM workout_plans_backup
                WHERE user_id IS NOT NULL
            """))
            db.session.commit()

            result = db.session.execute(text("SELECT COUNT(*) as count FROM workout_plans"))
            migrated_count = result.fetchone()[0]
            print(f"   ✓ Migrated {migrated_count} workout plans")
        else:
            print("   ✓ No data to migrate")

        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)
        print(f"Plans backed up: {backup_count}")
        result = db.session.execute(text("SELECT COUNT(*) as count FROM workout_plans"))
        final_count = result.fetchone()[0]
        print(f"Plans in new table: {final_count}")
        print("\nYou can now test the workout functionality.")
        print("Backup table 'workout_plans_backup' has been kept for safety.")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
