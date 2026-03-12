-- Migration to fix workout_plans table structure
-- This aligns the database table with the SQLAlchemy WorkoutPlan model

USE fitness_app;

-- Step 1: Backup existing data
CREATE TABLE IF NOT EXISTS workout_plans_backup AS SELECT * FROM workout_plans;

-- Step 2: Drop foreign key constraints on dependent tables
ALTER TABLE workout_days DROP FOREIGN KEY IF EXISTS workout_days_ibfk_1;
ALTER TABLE plan_exercises DROP FOREIGN KEY IF EXISTS plan_exercises_ibfk_1;

-- Step 3: Drop and recreate workout_plans table with correct structure
DROP TABLE IF EXISTS workout_plans;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Step 4: Restore foreign key constraints on dependent tables
ALTER TABLE workout_days
    ADD CONSTRAINT workout_days_ibfk_1
    FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE;

-- Step 5: Migrate data from backup (if any exists)
-- Map user_id to coach_id, compose description from goal/type/difficulty
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
WHERE user_id IS NOT NULL;

-- Step 6: Show migration results
SELECT 'Migration completed!' as Status;
SELECT COUNT(*) as 'Plans migrated' FROM workout_plans;
SELECT COUNT(*) as 'Plans in backup' FROM workout_plans_backup;

-- Optional: Drop backup table after verification
-- DROP TABLE workout_plans_backup;
