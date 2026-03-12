"""
Migration script to fix exercises table structure to match Exercise model
Run this with: python migrate_exercises_schema.py
"""
from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting exercises table schema migration...")

    try:
        # Check current structure
        print("1. Checking current exercises structure...")
        result = db.session.execute(text("DESCRIBE exercises"))
        columns = [row[0] for row in result.fetchall()]
        print(f"   Current columns: {', '.join(columns)}")

        # Check if there's any data in the table
        result = db.session.execute(text("SELECT COUNT(*) as count FROM exercises"))
        count = result.fetchone()[0]
        print(f"   Found {count} existing exercises")

        if count > 0:
            print("\n2. Backing up existing data...")
            db.session.execute(text("DROP TABLE IF EXISTS exercises_backup"))
            db.session.execute(text("""
                CREATE TABLE exercises_backup AS
                SELECT * FROM exercises
            """))
            db.session.commit()
            print(f"   ✓ Backed up {count} exercises")

        # Add missing columns
        changes_made = False

        # Add category column if missing
        if 'category' not in columns:
            print("\n3. Adding 'category' column...")
            db.session.execute(text("""
                ALTER TABLE exercises
                ADD COLUMN category ENUM('cardio', 'strength', 'flexibility', 'balance', 'sports')
                AFTER description
            """))
            db.session.commit()
            print("   ✓ Added category column")
            changes_made = True

        # Add video_url column if missing
        if 'video_url' not in columns:
            print("\n4. Adding 'video_url' column...")
            db.session.execute(text("""
                ALTER TABLE exercises
                ADD COLUMN video_url VARCHAR(255)
                AFTER difficulty
            """))
            db.session.commit()
            print("   ✓ Added video_url column")
            changes_made = True

        # Replace 'approved' with 'is_public' if needed
        if 'approved' in columns and 'is_public' not in columns:
            print("\n5. Replacing 'approved' with 'is_public'...")
            # Add is_public column
            db.session.execute(text("""
                ALTER TABLE exercises
                ADD COLUMN is_public BOOLEAN DEFAULT TRUE
                AFTER created_by
            """))
            # Copy approved values to is_public
            db.session.execute(text("""
                UPDATE exercises
                SET is_public = approved
            """))
            # Drop approved column
            db.session.execute(text("""
                ALTER TABLE exercises
                DROP COLUMN approved
            """))
            db.session.commit()
            print("   ✓ Replaced 'approved' with 'is_public'")
            changes_made = True
        elif 'is_public' not in columns:
            print("\n5. Adding 'is_public' column...")
            db.session.execute(text("""
                ALTER TABLE exercises
                ADD COLUMN is_public BOOLEAN DEFAULT TRUE
                AFTER created_by
            """))
            db.session.commit()
            print("   ✓ Added is_public column")
            changes_made = True

        # Add created_at column if missing
        if 'created_at' not in columns:
            print("\n6. Adding 'created_at' column...")
            db.session.execute(text("""
                ALTER TABLE exercises
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            db.session.commit()
            print("   ✓ Added created_at column")
            changes_made = True

        # Show final structure
        print("\n7. Final structure:")
        result = db.session.execute(text("DESCRIBE exercises"))
        for row in result.fetchall():
            print(f"   {row[0]}: {row[1]}")

        print("\n" + "="*60)
        if changes_made:
            print("Migration completed successfully!")
        else:
            print("No changes needed - table already up to date!")
        print("="*60)
        if count > 0:
            print(f"Old data backed up to: exercises_backup ({count} records)")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
