-- Fitness App Database Schema
-- MySQL Database Creation Script

-- Create database
CREATE DATABASE IF NOT EXISTS fitness_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fitness_app;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS chat_reports;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS admin_audit_log;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS mood_surveys;
DROP TABLE IF EXISTS meal_plan_items;
DROP TABLE IF EXISTS meal_plans;
DROP TABLE IF EXISTS meals;
DROP TABLE IF EXISTS daily_metrics;
DROP TABLE IF EXISTS workout_logs;
DROP TABLE IF EXISTS calendar_workouts;
DROP TABLE IF EXISTS workout_plan_exercises;
DROP TABLE IF EXISTS workout_plans;
DROP TABLE IF EXISTS exercises;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS client_requests;
DROP TABLE IF EXISTS coach_relationships;
DROP TABLE IF EXISTS coach_pricing;
DROP TABLE IF EXISTS coach_availability;
DROP TABLE IF EXISTS coach_specializations;
DROP TABLE IF EXISTS specializations;
DROP TABLE IF EXISTS coach_surveys;
DROP TABLE IF EXISTS coach_applications;
DROP TABLE IF EXISTS user_goals;
DROP TABLE IF EXISTS fitness_surveys;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS users;

-- ============================================
-- PHASE 1: Users & Authentication
-- ============================================

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('client', 'coach', 'both', 'admin') DEFAULT NULL,
    status ENUM('active', 'disabled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_picture VARCHAR(255),
    bio TEXT,
    phone VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE fitness_surveys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    weight DECIMAL(5,2),
    age INT,
    fitness_level ENUM('beginner', 'intermediate', 'advanced'),
    goals TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_goals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    goal_type VARCHAR(100),
    target_value VARCHAR(255),
    target_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 2: Coach System
-- ============================================

CREATE TABLE specializations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_applications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    status ENUM('pending', 'approved', 'denied') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    admin_id INT NULL,
    admin_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_status (status),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_surveys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    experience_years INT,
    certifications TEXT,
    bio TEXT,
    specialization_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_specializations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    coach_id INT NOT NULL,
    specialization_id INT NOT NULL,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (specialization_id) REFERENCES specializations(id),
    UNIQUE KEY unique_coach_specialization (coach_id, specialization_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_specialization_id (specialization_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_availability (
    id INT PRIMARY KEY AUTO_INCREMENT,
    coach_id INT NOT NULL,
    day_of_week INT CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_coach_id (coach_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_pricing (
    id INT PRIMARY KEY AUTO_INCREMENT,
    coach_id INT NOT NULL,
    session_type VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_coach_id (coach_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Client-Coach Relationships
-- ============================================

CREATE TABLE client_requests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    coach_id INT NOT NULL,
    status ENUM('pending', 'accepted', 'denied') DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_client_id (client_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE coach_relationships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    coach_id INT NOT NULL,
    status ENUM('active', 'ended') DEFAULT 'active',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_active_client_coach (client_id, status),
    INDEX idx_client_id (client_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    coach_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_coach_id (coach_id),
    INDEX idx_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    reporter_id INT NOT NULL,
    reported_id INT NOT NULL,
    report_type ENUM('coach', 'message', 'other'),
    reason TEXT NOT NULL,
    status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (reported_id) REFERENCES users(id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 3: Messaging
-- ============================================

CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    relationship_id INT NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (relationship_id) REFERENCES coach_relationships(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    INDEX idx_relationship_id (relationship_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chat_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    message_id INT NOT NULL,
    reporter_id INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('pending', 'reviewed') DEFAULT 'pending',
    reviewed_by INT NULL,
    reviewed_at TIMESTAMP NULL,
    FOREIGN KEY (message_id) REFERENCES chat_messages(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 4: Workouts & Exercises
-- ============================================

CREATE TABLE exercises (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    equipment VARCHAR(100),
    difficulty ENUM('beginner', 'intermediate', 'advanced'),
    muscle_group VARCHAR(100),
    instructions TEXT,
    created_by INT,
    approved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_equipment (equipment),
    INDEX idx_difficulty (difficulty),
    INDEX idx_muscle_group (muscle_group),
    INDEX idx_approved (approved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workout_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    name VARCHAR(255) NOT NULL,
    goal VARCHAR(100),
    difficulty ENUM('beginner', 'intermediate', 'advanced'),
    duration_minutes INT,
    type VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_goal (goal),
    INDEX idx_difficulty (difficulty),
    INDEX idx_is_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workout_plan_exercises (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plan_id INT NOT NULL,
    exercise_id INT NOT NULL,
    sets INT,
    reps INT,
    order_num INT,
    notes TEXT,
    FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    INDEX idx_plan_id (plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE calendar_workouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    workout_plan_id INT NOT NULL,
    scheduled_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plans(id),
    INDEX idx_user_id (user_id),
    INDEX idx_scheduled_date (scheduled_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE workout_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    exercise_id INT NOT NULL,
    log_date DATE NOT NULL,
    sets INT,
    reps INT,
    weight DECIMAL(6,2),
    duration_minutes INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id),
    INDEX idx_user_id (user_id),
    INDEX idx_log_date (log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 5: Nutrition & Wellness
-- ============================================

CREATE TABLE daily_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    steps INT,
    calories_burned INT,
    water_intake_ml INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (user_id, log_date),
    INDEX idx_user_id (user_id),
    INDEX idx_log_date (log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE meals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    meal_time TIME NOT NULL,
    description TEXT,
    calories INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_log_date (log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE meal_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE meal_plan_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    meal_plan_id INT NOT NULL,
    meal_name VARCHAR(255),
    description TEXT,
    calories INT,
    order_num INT,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
    INDEX idx_meal_plan_id (meal_plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mood_surveys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    mood_score INT CHECK (mood_score >= 1 AND mood_score <= 10),
    energy_level INT CHECK (energy_level >= 1 AND energy_level <= 10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (user_id, log_date),
    INDEX idx_user_id (user_id),
    INDEX idx_log_date (log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 9: Payments
-- ============================================

CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id INT NOT NULL,
    coach_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status ENUM('pending', 'succeeded', 'failed', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(255) UNIQUE,
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(id),
    FOREIGN KEY (coach_id) REFERENCES users(id),
    INDEX idx_client_id (client_id),
    INDEX idx_coach_id (coach_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE payment_methods (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type VARCHAR(50),
    last4 VARCHAR(4),
    expiry VARCHAR(7),
    token VARCHAR(255),
    is_default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PHASE 10: Notifications & Admin
-- ============================================

CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    read_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_read_status (read_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE admin_audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_admin_id (admin_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
