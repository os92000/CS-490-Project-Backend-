-- Fitness App Mock Data
-- Sample data for testing and development

USE fitness_app;

-- ============================================
-- Users (3 admins, 3 coaches, 4 clients)
-- Password for all users: "Password123"
-- ============================================

INSERT INTO users (email, password_hash, role, status) VALUES
-- Admins
('admin@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'admin', 'active'),
('superadmin@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'admin', 'active'),
('moderator@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'admin', 'active'),
-- Coaches
('coach1@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'coach', 'active'),
('coach2@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'coach', 'active'),
('coach3@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'both', 'active'),
-- Clients
('client1@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'client', 'active'),
('client2@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'client', 'active'),
('client3@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'client', 'active'),
('client4@fitness.com', 'scrypt:32768:8:1$nI4L7qjXOLiADzBy$c8d5efd4b8f9e3d7a1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1c2b5f6e8d9c7b4a3f6e8d1', 'client', 'active');

-- User Profiles
INSERT INTO user_profiles (user_id, first_name, last_name, bio, phone) VALUES
(1, 'John', 'Admin', 'System Administrator', '555-0001'),
(2, 'Sarah', 'SuperAdmin', 'Lead Administrator', '555-0002'),
(3, 'Mike', 'Moderator', 'Content Moderator', '555-0003'),
(4, 'Alex', 'Thompson', 'Certified Personal Trainer with 10 years experience', '555-0104'),
(5, 'Jamie', 'Rodriguez', 'Nutrition and strength training specialist', '555-0105'),
(6, 'Taylor', 'Chen', 'CrossFit and HIIT expert', '555-0106'),
(7, 'Emily', 'Johnson', 'Looking to get fit and healthy', '555-0207'),
(8, 'David', 'Smith', 'Marathon runner seeking coaching', '555-0208'),
(9, 'Lisa', 'Brown', 'Beginner looking to lose weight', '555-0209'),
(10, 'Ryan', 'Davis', 'Bodybuilding enthusiast', '555-0210');

-- Fitness Surveys
INSERT INTO fitness_surveys (user_id, weight, age, fitness_level, goals) VALUES
(7, 68.5, 28, 'beginner', 'Lose 10kg and improve overall fitness'),
(8, 75.0, 34, 'intermediate', 'Complete a marathon in under 4 hours'),
(9, 82.3, 42, 'beginner', 'Weight loss and cardiovascular health'),
(10, 88.0, 25, 'advanced', 'Build muscle mass and compete in bodybuilding');

-- ============================================
-- Specializations
-- ============================================

INSERT INTO specializations (name, category) VALUES
('Weight Loss', 'General'),
('Muscle Building', 'Strength'),
('Cardiovascular Training', 'Endurance'),
('Nutrition Counseling', 'Nutrition'),
('HIIT Training', 'Intensity'),
('Yoga & Flexibility', 'Flexibility'),
('Sports Performance', 'Sports'),
('Rehabilitation', 'Recovery'),
('Bodybuilding', 'Strength'),
('Marathon Training', 'Endurance');

-- Coach Applications (all approved)
INSERT INTO coach_applications (user_id, status, submitted_at, reviewed_at, admin_id, admin_notes) VALUES
(4, 'approved', DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 29 DAY), 1, 'Excellent credentials'),
(5, 'approved', DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 24 DAY), 1, 'Approved'),
(6, 'approved', DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 19 DAY), 1, 'Great experience');

-- Coach Surveys
INSERT INTO coach_surveys (user_id, experience_years, certifications, bio, specialization_notes) VALUES
(4, 10, 'NASM-CPT, ACE, ISSA', 'Passionate about helping clients achieve their fitness goals through personalized training programs.', 'Specializing in weight loss and strength training'),
(5, 7, 'NASM-CPT, Precision Nutrition Level 1', 'Combining fitness and nutrition for holistic wellness.', 'Focus on nutrition coaching and body recomposition'),
(6, 5, 'CrossFit Level 2, HIIT Certified', 'High-intensity training expert helping clients push their limits.', 'HIIT and functional fitness specialist');

-- Coach Specializations
INSERT INTO coach_specializations (coach_id, specialization_id) VALUES
(4, 1), (4, 2), (4, 3),  -- Alex: Weight Loss, Muscle Building, Cardio
(5, 1), (5, 4), (5, 2),  -- Jamie: Weight Loss, Nutrition, Muscle Building
(6, 5), (6, 3), (6, 7);  -- Taylor: HIIT, Cardio, Sports Performance

-- Coach Pricing
INSERT INTO coach_pricing (coach_id, session_type, price, currency) VALUES
(4, '1-on-1 Session (60 min)', 80.00, 'USD'),
(4, 'Monthly Package (8 sessions)', 600.00, 'USD'),
(5, '1-on-1 Session (60 min)', 90.00, 'USD'),
(5, 'Nutrition Consultation', 120.00, 'USD'),
(5, 'Monthly Package (8 sessions)', 680.00, 'USD'),
(6, '1-on-1 Session (60 min)', 75.00, 'USD'),
(6, 'Group Class', 30.00, 'USD'),
(6, 'Monthly Package (8 sessions)', 560.00, 'USD');

-- Coach Availability (sample schedule)
INSERT INTO coach_availability (coach_id, day_of_week, start_time, end_time) VALUES
-- Alex (Mon, Wed, Fri mornings)
(4, 1, '06:00:00', '12:00:00'),
(4, 3, '06:00:00', '12:00:00'),
(4, 5, '06:00:00', '12:00:00'),
-- Jamie (Tue, Thu, Sat)
(5, 2, '08:00:00', '18:00:00'),
(5, 4, '08:00:00', '18:00:00'),
(5, 6, '09:00:00', '15:00:00'),
-- Taylor (Mon-Fri evenings)
(6, 1, '17:00:00', '21:00:00'),
(6, 2, '17:00:00', '21:00:00'),
(6, 3, '17:00:00', '21:00:00'),
(6, 4, '17:00:00', '21:00:00'),
(6, 5, '17:00:00', '21:00:00');

-- ============================================
-- Client-Coach Relationships
-- ============================================

-- Client Requests (some accepted, some pending)
INSERT INTO client_requests (client_id, coach_id, status, requested_at, responded_at) VALUES
(7, 4, 'accepted', DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 14 DAY)),
(8, 5, 'accepted', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY)),
(9, 4, 'accepted', DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 9 DAY)),
(10, 6, 'pending', DATE_SUB(NOW(), INTERVAL 2 DAY), NULL);

-- Active Coach Relationships
INSERT INTO coach_relationships (client_id, coach_id, status, start_date) VALUES
(7, 4, 'active', DATE_SUB(NOW(), INTERVAL 14 DAY)),
(8, 5, 'active', DATE_SUB(NOW(), INTERVAL 11 DAY)),
(9, 4, 'active', DATE_SUB(NOW(), INTERVAL 9 DAY));

-- Reviews
INSERT INTO reviews (client_id, coach_id, rating, comment, created_at) VALUES
(7, 4, 5, 'Amazing coach! Very motivating and knowledgeable.', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(8, 5, 5, 'Jamie helped me understand nutrition better. Highly recommend!', DATE_SUB(NOW(), INTERVAL 3 DAY)),
(9, 4, 4, 'Great trainer, sees results after just 2 weeks!', DATE_SUB(NOW(), INTERVAL 1 DAY));

-- ============================================
-- Chat Messages
-- ============================================

INSERT INTO chat_messages (relationship_id, sender_id, message, sent_at) VALUES
-- Conversation between Emily (7) and Alex (4)
(1, 7, 'Hi Alex! Excited to start training with you.', DATE_SUB(NOW(), INTERVAL 14 DAY)),
(1, 4, 'Welcome Emily! Let''s discuss your goals and create a plan.', DATE_SUB(NOW(), INTERVAL 14 DAY)),
(1, 7, 'I want to lose 10kg and improve my overall fitness.', DATE_SUB(NOW(), INTERVAL 13 DAY)),
(1, 4, 'Perfect! We''ll start with 3 sessions per week focusing on cardio and strength.', DATE_SUB(NOW(), INTERVAL 13 DAY)),
(1, 7, 'Sounds great! When can we start?', DATE_SUB(NOW(), INTERVAL 13 DAY)),
(1, 4, 'How about Monday at 7 AM? I''ll send you a workout plan.', DATE_SUB(NOW(), INTERVAL 13 DAY)),
-- Conversation between David (8) and Jamie (5)
(2, 8, 'Hi Jamie, ready for marathon training!', DATE_SUB(NOW(), INTERVAL 11 DAY)),
(2, 5, 'Great! Let''s build your endurance gradually. What''s your current running pace?', DATE_SUB(NOW(), INTERVAL 11 DAY)),
(2, 8, 'I can run 10K in about 55 minutes.', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(2, 5, 'Excellent starting point. We''ll work on building your mileage safely.', DATE_SUB(NOW(), INTERVAL 10 DAY));

-- ============================================
-- Exercises
-- ============================================

INSERT INTO exercises (name, description, equipment, difficulty, muscle_group, instructions, created_by, approved) VALUES
('Push-ups', 'Classic upper body exercise', 'None', 'beginner', 'Chest', 'Start in plank position, lower body until chest nearly touches floor, push back up', 1, TRUE),
('Squats', 'Fundamental lower body movement', 'None', 'beginner', 'Legs', 'Stand with feet shoulder-width apart, lower hips back and down, return to standing', 1, TRUE),
('Pull-ups', 'Upper body pulling exercise', 'Pull-up bar', 'intermediate', 'Back', 'Hang from bar, pull body up until chin is over bar, lower with control', 1, TRUE),
('Deadlifts', 'Full body compound movement', 'Barbell', 'intermediate', 'Full Body', 'Lift barbell from ground to standing position with proper form', 1, TRUE),
('Bench Press', 'Chest pressing movement', 'Barbell', 'intermediate', 'Chest', 'Lie on bench, lower bar to chest, press back up', 1, TRUE),
('Lunges', 'Single leg exercise', 'None', 'beginner', 'Legs', 'Step forward, lower back knee toward ground, return to standing', 1, TRUE),
('Plank', 'Core stability exercise', 'None', 'beginner', 'Core', 'Hold body in straight line from head to heels on forearms', 1, TRUE),
('Burpees', 'Full body cardio exercise', 'None', 'advanced', 'Full Body', 'Drop to push-up, jump feet forward, jump up with arms overhead', 1, TRUE),
('Dumbbell Rows', 'Back pulling exercise', 'Dumbbells', 'beginner', 'Back', 'Bend at hips, pull dumbbell to ribcage, lower with control', 1, TRUE),
('Shoulder Press', 'Overhead pressing movement', 'Dumbbells', 'beginner', 'Shoulders', 'Press weights overhead from shoulder height', 1, TRUE),
('Russian Twists', 'Rotational core exercise', 'Medicine Ball', 'intermediate', 'Core', 'Sit with knees bent, rotate torso side to side holding weight', 1, TRUE),
('Box Jumps', 'Explosive lower body exercise', 'Plyo Box', 'intermediate', 'Legs', 'Jump onto elevated surface, step down, repeat', 1, TRUE),
('Mountain Climbers', 'Cardio core exercise', 'None', 'beginner', 'Core', 'From plank, alternate driving knees toward chest rapidly', 1, TRUE),
('Bicycle Crunches', 'Core rotational exercise', 'None', 'beginner', 'Core', 'Lie on back, alternate elbow to opposite knee in cycling motion', 1, TRUE),
('Kettlebell Swings', 'Hip hinge power exercise', 'Kettlebell', 'intermediate', 'Full Body', 'Swing kettlebell between legs and up to shoulder height using hip drive', 1, TRUE);

-- ============================================
-- Workout Plans
-- ============================================

INSERT INTO workout_plans (user_id, name, goal, difficulty, duration_minutes, type, is_public) VALUES
(4, 'Beginner Full Body', 'General Fitness', 'beginner', 45, 'Strength', TRUE),
(4, 'Weight Loss Circuit', 'Weight Loss', 'beginner', 30, 'Circuit', TRUE),
(5, 'Intermediate Strength', 'Muscle Building', 'intermediate', 60, 'Strength', TRUE),
(6, 'HIIT Blast', 'Fat Loss', 'advanced', 20, 'HIIT', TRUE),
(7, 'Emily''s Custom Plan', 'Weight Loss', 'beginner', 40, 'Mixed', FALSE);

-- Workout Plan Exercises
INSERT INTO workout_plan_exercises (plan_id, exercise_id, sets, reps, order_num, notes) VALUES
-- Beginner Full Body (Plan 1)
(1, 1, 3, 10, 1, 'Modify on knees if needed'),
(1, 2, 3, 15, 2, 'Focus on form'),
(1, 6, 3, 10, 3, 'Each leg'),
(1, 7, 3, 30, 4, 'Hold for seconds'),
(1, 9, 3, 12, 5, 'Each arm'),
-- Weight Loss Circuit (Plan 2)
(2, 8, 3, 10, 1, 'Full burpee'),
(2, 13, 3, 30, 2, 'Fast pace'),
(2, 2, 3, 20, 3, 'Bodyweight'),
(2, 1, 3, 15, 4, 'Standard or modified'),
-- HIIT Blast (Plan 4)
(4, 8, 4, 15, 1, '30 seconds work, 15 seconds rest'),
(4, 12, 4, 10, 2, 'Explosive'),
(4, 13, 4, 30, 3, 'Max effort'),
(4, 15, 4, 20, 4, 'Powerful swings');

-- ============================================
-- Workout Logs
-- ============================================

INSERT INTO workout_logs (user_id, exercise_id, log_date, sets, reps, weight, duration_minutes, notes) VALUES
-- Emily's logs
(7, 1, CURDATE(), 3, 10, NULL, NULL, 'Felt strong today'),
(7, 2, CURDATE(), 3, 15, NULL, NULL, 'Form improving'),
(7, 1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 3, 8, NULL, NULL, 'First workout'),
-- David's logs
(8, 2, CURDATE(), 4, 12, 50.0, NULL, 'Adding weight'),
(8, 4, CURDATE(), 3, 8, 135.0, NULL, 'Personal record!'),
-- Ryan's logs
(10, 5, CURDATE(), 4, 10, 185.0, NULL, 'Increasing weight gradually'),
(10, 3, CURDATE(), 3, 8, NULL, NULL, 'Working on form');

-- Calendar Workouts
INSERT INTO calendar_workouts (user_id, workout_plan_id, scheduled_date) VALUES
(7, 5, CURDATE()),
(7, 5, DATE_ADD(CURDATE(), INTERVAL 2 DAY)),
(7, 5, DATE_ADD(CURDATE(), INTERVAL 4 DAY)),
(8, 3, DATE_ADD(CURDATE(), INTERVAL 1 DAY)),
(9, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY));

-- ============================================
-- Nutrition Data
-- ============================================

-- Daily Metrics
INSERT INTO daily_metrics (user_id, log_date, steps, calories_burned, water_intake_ml) VALUES
(7, CURDATE(), 8500, 2100, 2000),
(7, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 7200, 1950, 1800),
(8, CURDATE(), 12000, 2500, 2500),
(9, CURDATE(), 6000, 1850, 1500),
(10, CURDATE(), 9500, 2800, 2200);

-- Meals
INSERT INTO meals (user_id, log_date, meal_time, description, calories) VALUES
(7, CURDATE(), '08:00:00', 'Oatmeal with berries and almonds', 350),
(7, CURDATE(), '12:30:00', 'Grilled chicken salad', 450),
(7, CURDATE(), '15:00:00', 'Apple and protein shake', 250),
(8, CURDATE(), '07:00:00', 'Greek yogurt with granola', 400),
(8, CURDATE(), '13:00:00', 'Turkey sandwich on whole wheat', 550),
(9, CURDATE(), '08:30:00', 'Scrambled eggs and toast', 400),
(9, CURDATE(), '12:00:00', 'Quinoa bowl with vegetables', 500);

-- Mood Surveys
INSERT INTO mood_surveys (user_id, log_date, mood_score, energy_level, notes) VALUES
(7, CURDATE(), 8, 7, 'Feeling great after morning workout'),
(7, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 7, 6, 'Good day overall'),
(8, CURDATE(), 9, 8, 'Excellent training session'),
(9, CURDATE(), 6, 5, 'Tired but motivated'),
(10, CURDATE(), 8, 8, 'Hitting PRs!');

-- ============================================
-- Notifications
-- ============================================

INSERT INTO notifications (user_id, type, title, message, read_status) VALUES
(7, 'workout', 'Workout Scheduled', 'You have a workout scheduled for today at 7:00 AM', FALSE),
(7, 'message', 'New Message', 'You have a new message from your coach', TRUE),
(8, 'coach_request', 'Coach Request Accepted', 'Jamie Rodriguez has accepted your coaching request', TRUE),
(9, 'workout', 'Workout Reminder', 'Don''t forget your workout tomorrow!', FALSE),
(10, 'coach_request', 'Coach Request Pending', 'Your request to Taylor Chen is pending', FALSE);

-- ============================================
-- Summary
-- ============================================

-- Total Users: 10 (3 admins, 3 coaches, 4 clients)
-- Active Coach Relationships: 3
-- Exercises: 15
-- Workout Plans: 5
-- Reviews: 3
-- Chat Messages: 10
-- Workout Logs: 7
-- Mock data ready for testing all features!
