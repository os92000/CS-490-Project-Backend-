-- Seed Data for Fitness App Demo
-- This creates permanent demo data including coaches, exercises, and sample content

USE fitness_app;

-- Insert Specializations
INSERT INTO specializations (name, category) VALUES
('Weight Loss', 'fitness'),
('Muscle Gain', 'fitness'),
('Cardio Training', 'fitness'),
('Strength Training', 'fitness'),
('Yoga & Flexibility', 'wellness'),
('Sports Performance', 'athletic'),
('Senior Fitness', 'specialized'),
('Injury Recovery', 'rehabilitation'),
('Nutrition Coaching', 'nutrition'),
('CrossFit', 'fitness');

-- Insert Demo Coaches (with hashed password: "Demo123!")
-- Password hash for "Demo123!"
SET @demo_password = 'scrypt:32768:8:1$yxoJZWn2kxL3UWGK$c3ecbf6d8e5a4f9e2b1c7d6a8f3e9b2c4d5a7e1f8b3c6d9a2e5f7b1c4d8a3e6f9b2c5d7a1e4f8b3c6d9a2e5f';

-- Demo Coach 1: Sarah Johnson - Weight Loss Expert
INSERT INTO users (email, password_hash, role, status) VALUES
('sarah.johnson@demo.fit', @demo_password, 'coach', 'active');
SET @coach1_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone, profile_picture) VALUES
(@coach1_id, 'Sarah', 'Johnson', 'Certified personal trainer with 8+ years of experience specializing in weight loss transformation. Helped over 200 clients achieve their fitness goals through personalized programs.', '+1-555-0101', NULL);

INSERT INTO coach_surveys (user_id, experience_years, certifications, bio, specialization_notes) VALUES
(@coach1_id, 8, 'ACE Certified Personal Trainer, Nutrition Specialist', 'Expert in creating sustainable weight loss programs that focus on lifestyle changes rather than quick fixes.', 'Weight loss, nutrition planning, habit building');

INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(@coach1_id, 1), -- Weight Loss
(@coach1_id, 9); -- Nutrition Coaching

INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(@coach1_id, '1-on-1 Session', 75.00, 'USD'),
(@coach1_id, 'Monthly Package', 250.00, 'USD'),
(@coach1_id, 'Group Session', 35.00, 'USD');

-- Demo Coach 2: Marcus Rodriguez - Strength Training
INSERT INTO users (email, password_hash, role, status) VALUES
('marcus.rodriguez@demo.fit', @demo_password, 'coach', 'active');
SET @coach2_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone) VALUES
(@coach2_id, 'Marcus', 'Rodriguez', 'Former competitive powerlifter and strength coach. Passionate about helping people build strength and confidence through progressive training programs.', '+1-555-0102');

INSERT INTO coach_surveys (user_id, experience_years, certifications, bio) VALUES
(@coach2_id, 10, 'NSCA-CSCS, USA Powerlifting Coach', 'Specialized in strength training, powerlifting, and muscle building with proven track record.');

INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(@coach2_id, 2), -- Muscle Gain
(@coach2_id, 4); -- Strength Training

INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(@coach2_id, '1-on-1 Session', 85.00, 'USD'),
(@coach2_id, 'Monthly Package', 300.00, 'USD');

-- Demo Coach 3: Emily Chen - Yoga & Wellness
INSERT INTO users (email, password_hash, role, status) VALUES
('emily.chen@demo.fit', @demo_password, 'coach', 'active');
SET @coach3_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone) VALUES
(@coach3_id, 'Emily', 'Chen', 'Certified yoga instructor and wellness coach focusing on mind-body connection. Specializes in flexibility, stress reduction, and holistic health.', '+1-555-0103');

INSERT INTO coach_surveys (user_id, experience_years, certifications, bio) VALUES
(@coach3_id, 6, 'RYT-500, Wellness Coach Certification', 'Creating balanced fitness programs that integrate yoga, meditation, and functional movement.');

INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(@coach3_id, 5); -- Yoga & Flexibility

INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(@coach3_id, '1-on-1 Session', 65.00, 'USD'),
(@coach3_id, 'Monthly Package', 220.00, 'USD'),
(@coach3_id, 'Group Class', 25.00, 'USD');

-- Demo Coach 4: David Thompson - Sports Performance
INSERT INTO users (email, password_hash, role, status) VALUES
('david.thompson@demo.fit', @demo_password, 'coach', 'active');
SET @coach4_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone) VALUES
(@coach4_id, 'David', 'Thompson', 'Sports performance coach working with athletes from high school to professional level. Expert in speed, agility, and sport-specific conditioning.', '+1-555-0104');

INSERT INTO coach_surveys (user_id, experience_years, certifications, bio) VALUES
(@coach4_id, 12, 'CSCS, USAW Sports Performance Coach', 'Former collegiate athlete now helping others reach peak performance in their sport.');

INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(@coach4_id, 6), -- Sports Performance
(@coach4_id, 4); -- Strength Training

INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(@coach4_id, '1-on-1 Session', 95.00, 'USD'),
(@coach4_id, 'Monthly Package', 350.00, 'USD');

-- Demo Coach 5: Lisa Martinez - Senior Fitness
INSERT INTO users (email, password_hash, role, status) VALUES
('lisa.martinez@demo.fit', @demo_password, 'coach', 'active');
SET @coach5_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone) VALUES
(@coach5_id, 'Lisa', 'Martinez', 'Specialized in senior fitness and functional training. Focused on improving mobility, balance, and quality of life for older adults.', '+1-555-0105');

INSERT INTO coach_surveys (user_id, experience_years, certifications, bio) VALUES
(@coach5_id, 7, 'Senior Fitness Specialist, ACE Certified', 'Compassionate approach to helping seniors maintain independence through fitness.');

INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(@coach5_id, 7), -- Senior Fitness
(@coach5_id, 8); -- Injury Recovery

INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(@coach5_id, '1-on-1 Session', 70.00, 'USD'),
(@coach5_id, 'Monthly Package', 240.00, 'USD');

-- Add Sample Reviews for Coaches
INSERT INTO reviews (client_id, coach_id, rating, comment, created_at) VALUES
-- Reviews for Sarah (Weight Loss)
(@coach1_id, @coach1_id, 5, 'Sarah helped me lose 30 pounds in 4 months! Her approach is sustainable and she really cares about her clients.', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(@coach1_id, @coach1_id, 5, 'Best coach I have ever worked with. Very knowledgeable and supportive throughout my journey.', DATE_SUB(NOW(), INTERVAL 60 DAY)),
(@coach1_id, @coach1_id, 4, 'Great coach! Very professional and creates personalized plans. Would recommend.', DATE_SUB(NOW(), INTERVAL 90 DAY)),

-- Reviews for Marcus (Strength)
(@coach2_id, @coach2_id, 5, 'Marcus knows his stuff! Increased my deadlift by 100lbs in 6 months. Excellent programming.', DATE_SUB(NOW(), INTERVAL 45 DAY)),
(@coach2_id, @coach2_id, 5, 'If you want to get strong, Marcus is your guy. No nonsense approach that gets results.', DATE_SUB(NOW(), INTERVAL 20 DAY)),

-- Reviews for Emily (Yoga)
(@coach3_id, @coach3_id, 5, 'Emily is amazing! My flexibility has improved so much and I feel less stressed. Highly recommend!', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(@coach3_id, @coach3_id, 4, 'Very calming and knowledgeable instructor. Great for beginners and advanced students.', DATE_SUB(NOW(), INTERVAL 40 DAY)),

-- Reviews for David (Sports)
(@coach4_id, @coach4_id, 5, 'Helped improve my vertical jump and sprint speed significantly. Great for athletes!', DATE_SUB(NOW(), INTERVAL 25 DAY));

-- Insert Exercise Database
INSERT INTO exercises (name, description, category, muscle_group, equipment, difficulty, instructions, is_public) VALUES
-- Cardio Exercises
('Running', '30 minutes of steady-state running', 'cardio', 'full-body', 'none', 'beginner', 'Maintain steady pace for entire duration', true),
('Jump Rope', 'High-intensity jump rope intervals', 'cardio', 'full-body', 'jump rope', 'intermediate', 'Jump for 30 seconds, rest 30 seconds, repeat', true),
('Cycling', 'Stationary or outdoor cycling', 'cardio', 'legs', 'bike', 'beginner', 'Maintain moderate resistance and steady cadence', true),
('Rowing Machine', 'Full body cardio workout', 'cardio', 'full-body', 'rowing machine', 'intermediate', 'Focus on proper form: legs, core, arms', true),
('Burpees', 'Full body explosive movement', 'cardio', 'full-body', 'bodyweight', 'advanced', 'Squat, plank, push-up, jump. Repeat continuously', true),

-- Strength Exercises
('Barbell Squat', 'Compound lower body exercise', 'strength', 'legs', 'barbell', 'intermediate', 'Keep chest up, squat to parallel or below, drive through heels', true),
('Bench Press', 'Upper body pushing exercise', 'strength', 'chest', 'barbell', 'intermediate', 'Lower bar to chest, press up explosively, keep elbows at 45 degrees', true),
('Deadlift', 'Posterior chain compound movement', 'strength', 'back', 'barbell', 'advanced', 'Hip hinge movement, keep back neutral, drive through floor', true),
('Pull-ups', 'Bodyweight back exercise', 'strength', 'back', 'pull-up bar', 'intermediate', 'Pull chin over bar, control descent, full extension at bottom', true),
('Push-ups', 'Upper body bodyweight exercise', 'strength', 'chest', 'bodyweight', 'beginner', 'Keep body straight, lower chest to ground, push back up', true),
('Dumbbell Shoulder Press', 'Shoulder strength exercise', 'strength', 'shoulders', 'dumbbells', 'beginner', 'Press dumbbells overhead, control descent, maintain core stability', true),
('Lunges', 'Single leg lower body exercise', 'strength', 'legs', 'bodyweight', 'beginner', 'Step forward, lower back knee to ground, drive back to start', true),
('Plank', 'Core stability exercise', 'strength', 'core', 'bodyweight', 'beginner', 'Hold straight body position on forearms, engage core and glutes', true),

-- Flexibility Exercises
('Hamstring Stretch', 'Lower body flexibility', 'flexibility', 'legs', 'none', 'beginner', 'Reach toward toes, hold for 30 seconds, breathe deeply', true),
('Cat-Cow Stretch', 'Spine mobility exercise', 'flexibility', 'back', 'none', 'beginner', 'Alternate between arching and rounding spine, sync with breath', true),
('Shoulder Circles', 'Upper body mobility', 'flexibility', 'shoulders', 'none', 'beginner', 'Make large circles with arms, both directions', true),
('Downward Dog', 'Full body yoga pose', 'flexibility', 'full-body', 'yoga mat', 'beginner', 'Form inverted V with body, press heels down, relax shoulders', true),
('Pigeon Pose', 'Hip flexibility yoga pose', 'flexibility', 'hips', 'yoga mat', 'intermediate', 'Bring knee forward, extend back leg, fold forward over front leg', true),

-- Balance Exercises
('Single Leg Stand', 'Basic balance exercise', 'balance', 'legs', 'none', 'beginner', 'Stand on one leg for 30 seconds, switch legs', true),
('Tree Pose', 'Yoga balance pose', 'balance', 'legs', 'yoga mat', 'beginner', 'Place foot on inner thigh, hands in prayer position, focus on single point', true);

-- Insert Sample Workout Plan (for demonstration)
INSERT INTO workout_plans (name, description, coach_id, client_id, start_date, end_date, status) VALUES
('Beginner Full Body Program', 'A balanced 3-day per week program for beginners focusing on foundational movements and building consistency.', @coach1_id, @coach1_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 8 WEEK), 'active');
SET @sample_plan_id = LAST_INSERT_ID();

-- Day 1: Upper Body Focus
INSERT INTO workout_days (plan_id, name, day_number, notes) VALUES
(@sample_plan_id, 'Day 1: Upper Body', 1, 'Focus on controlled movements and proper form');
SET @day1_id = LAST_INSERT_ID();

INSERT INTO plan_exercises (workout_day_id, exercise_id, `order`, sets, reps, rest_seconds, notes) VALUES
(@day1_id, 7, 1, 3, '8-10', 90, 'Warm up with empty bar first'),
(@day1_id, 10, 2, 3, '10-12', 60, 'Can use resistance band for assistance if needed'),
(@day1_id, 11, 3, 3, '10-12', 60, 'Keep core tight throughout'),
(@day1_id, 13, 4, 3, '30-60 seconds', 60, 'Hold strong plank position');

-- Day 2: Lower Body Focus
INSERT INTO workout_days (plan_id, name, day_number, notes) VALUES
(@sample_plan_id, 'Day 2: Lower Body', 2, 'Focus on depth and balance');
SET @day2_id = LAST_INSERT_ID();

INSERT INTO plan_exercises (workout_day_id, exercise_id, `order`, sets, reps, rest_seconds, notes) VALUES
(@day2_id, 6, 1, 3, '8-10', 120, 'Squat to at least parallel'),
(@day2_id, 12, 2, 3, '10-12 each leg', 60, 'Alternate legs or do all reps one side then switch'),
(@day2_id, 13, 3, 3, '30-60 seconds', 60, 'Finish with core work');

-- Day 3: Full Body
INSERT INTO workout_days (plan_id, name, day_number, notes) VALUES
(@sample_plan_id, 'Day 3: Full Body Circuit', 3, 'Moderate intensity, focus on movement quality');
SET @day3_id = LAST_INSERT_ID();

INSERT INTO plan_exercises (workout_day_id, exercise_id, `order`, sets, reps, rest_seconds, notes) VALUES
(@day3_id, 10, 1, 3, '8-10', 60, 'Push-ups for upper body'),
(@day3_id, 12, 2, 3, '10 each leg', 60, 'Lunges for lower body'),
(@day3_id, 5, 3, 3, '10', 90, 'Burpees for conditioning'),
(@day3_id, 13, 4, 3, '45 seconds', 60, 'Finish with core');

COMMIT;

-- Display summary
SELECT 'Seed data inserted successfully!' as Status;
SELECT COUNT(*) as 'Total Coaches' FROM users WHERE role IN ('coach', 'both');
SELECT COUNT(*) as 'Total Exercises' FROM exercises;
SELECT COUNT(*) as 'Total Reviews' FROM reviews;
SELECT COUNT(*) as 'Total Specializations' FROM specializations;
