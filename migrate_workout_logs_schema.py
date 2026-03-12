"""
Migration script to add client_id column to workout_logs table
Run this with: python migrate_workout_logs_schema.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting workout_logs schema migration...")

    try:
        # Check current structure
        print("1. Checking current workout_logs structure...")
        result = db.session.execute(text("DESCRIBE workout_logs"))
        columns = [row[0] for row in result.fetchall()]
        print(f"   Current columns: {', '.join(columns)}")

        if 'client_id' in columns:
            print("   ✓ client_id column already exists!")
        else:
            print("   ✗ client_id column is missing, will add it")

            # Check if there's any data in the table
            result = db.session.execute(text("SELECT COUNT(*) as count FROM workout_logs"))
            count = result.fetchone()[0]
            print(f"   Found {count} existing workout logs")

            if count > 0:
                print("\n2. Backing up existing data...")
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS workout_logs_backup AS
                    SELECT * FROM workout_logs
                """))
                db.session.commit()
                print(f"   ✓ Backed up {count} workout logs")

            # Add the client_id column
            print("\n3. Adding client_id column...")

            if count > 0:
                # If there's existing data, add as nullable first, then update it
                db.session.execute(text("""
                    ALTER TABLE workout_logs
                    ADD COLUMN client_id INT NULL
                    AFTER id
                """))
                db.session.commit()
                print("   ✓ Added client_id column (nullable)")

                # Try to populate client_id from user_id if it exists
                if 'user_id' in columns:
                    print("\n4. Migrating user_id to client_id...")
                    db.session.execute(text("""
                        UPDATE workout_logs
                        SET client_id = user_id
                        WHERE user_id IS NOT NULL
                    """))
                    db.session.commit()
                    print("   ✓ Migrated user_id to client_id")
                else:
                    # If no user_id, we need to set a default value or delete records
                    print("\n4. WARNING: No user_id column found to migrate from")
                    print("   Setting client_id to NULL for now - you may need to manually update these")

                # Now make it NOT NULL
                print("\n5. Making client_id NOT NULL...")
                # First check if there are any NULL values
                result = db.session.execute(text("SELECT COUNT(*) FROM workout_logs WHERE client_id IS NULL"))
                null_count = result.fetchone()[0]

                if null_count > 0:
                    print(f"   WARNING: {null_count} records have NULL client_id")
                    print("   Cannot make column NOT NULL. Please update these records first.")
                else:
                    db.session.execute(text("""
                        ALTER TABLE workout_logs
                        MODIFY COLUMN client_id INT NOT NULL
                    """))
                    db.session.commit()
                    print("   ✓ Made client_id NOT NULL")
            else:
                # No existing data, add column as NOT NULL directly
                db.session.execute(text("""
                    ALTER TABLE workout_logs
                    ADD COLUMN client_id INT NOT NULL
                    AFTER id
                """))
                db.session.commit()
                print("   ✓ Added client_id column (NOT NULL)")

            # Add foreign key constraint
            print("\n6. Adding foreign key constraint...")
            db.session.execute(text("""
                ALTER TABLE workout_logs
                ADD CONSTRAINT workout_logs_client_fk
                FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE
            """))
            db.session.commit()
            print("   ✓ Added foreign key constraint")

            # Show final structure
            print("\n7. Final structure:")
            result = db.session.execute(text("DESCRIBE workout_logs"))
            for row in result.fetchall():
                print(f"   {row[0]}: {row[1]}")

        print("\n" + "="*60)
        print("Migration completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
