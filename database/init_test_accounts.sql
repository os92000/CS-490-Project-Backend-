-- MySQL dump 10.13  Distrib 8.4.8, for Win64 (x86_64)
--
-- Host: localhost    Database: fitness_app
-- ------------------------------------------------------
-- Server version	8.4.8

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `body_metrics`
--

DROP TABLE IF EXISTS `body_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `body_metrics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `date` date NOT NULL,
  `weight_kg` decimal(5,2) DEFAULT NULL,
  `body_fat_percentage` decimal(4,2) DEFAULT NULL,
  `muscle_mass_kg` decimal(5,2) DEFAULT NULL,
  `chest_cm` decimal(5,2) DEFAULT NULL,
  `waist_cm` decimal(5,2) DEFAULT NULL,
  `hips_cm` decimal(5,2) DEFAULT NULL,
  `arms_cm` decimal(5,2) DEFAULT NULL,
  `thighs_cm` decimal(5,2) DEFAULT NULL,
  `notes` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `body_metrics_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `body_metrics`
--

LOCK TABLES `body_metrics` WRITE;
/*!40000 ALTER TABLE `body_metrics` DISABLE KEYS */;
/*!40000 ALTER TABLE `body_metrics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `calendar_notes`
--

DROP TABLE IF EXISTS `calendar_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `calendar_notes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `date` date NOT NULL,
  `note` text NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `calendar_notes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `calendar_notes`
--

LOCK TABLES `calendar_notes` WRITE;
/*!40000 ALTER TABLE `calendar_notes` DISABLE KEYS */;
/*!40000 ALTER TABLE `calendar_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `chat_messages`
--

DROP TABLE IF EXISTS `chat_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `relationship_id` int NOT NULL,
  `sender_id` int NOT NULL,
  `message` text NOT NULL,
  `sent_at` datetime DEFAULT NULL,
  `read_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `relationship_id` (`relationship_id`),
  KEY `sender_id` (`sender_id`),
  CONSTRAINT `chat_messages_ibfk_1` FOREIGN KEY (`relationship_id`) REFERENCES `coach_relationships` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chat_messages_ibfk_2` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chat_messages`
--

LOCK TABLES `chat_messages` WRITE;
/*!40000 ALTER TABLE `chat_messages` DISABLE KEYS */;
INSERT INTO `chat_messages` VALUES (1,1,7,'hi','2026-04-22 17:13:10','2026-04-22 17:16:48'),(2,1,2,'testing','2026-04-22 17:16:54','2026-04-22 17:16:59'),(3,1,7,'asdasasd','2026-04-22 17:17:03','2026-04-22 17:17:12'),(4,1,2,'testasdasd','2026-04-22 17:20:54',NULL),(5,1,7,'asdasdasd','2026-04-22 17:21:03',NULL),(6,4,2,'hello','2026-04-22 18:05:54','2026-04-22 18:05:59'),(7,4,8,'2','2026-04-22 18:06:03','2026-04-22 20:47:50'),(8,4,2,'3','2026-04-22 18:06:11','2026-04-22 20:47:28'),(9,4,8,'hello','2026-04-22 20:47:33','2026-04-22 20:47:50');
/*!40000 ALTER TABLE `chat_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_requests`
--

DROP TABLE IF EXISTS `client_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `status` enum('pending','accepted','denied') DEFAULT NULL,
  `requested_at` datetime DEFAULT NULL,
  `responded_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `client_requests_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `client_requests_ibfk_2` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_requests`
--

LOCK TABLES `client_requests` WRITE;
/*!40000 ALTER TABLE `client_requests` DISABLE KEYS */;
INSERT INTO `client_requests` VALUES (1,7,2,'accepted','2026-04-22 17:11:24','2026-04-22 13:11:24'),(2,8,2,'accepted','2026-04-22 17:50:51','2026-04-22 13:50:50'),(3,8,2,'accepted','2026-04-22 17:56:37','2026-04-22 13:56:42'),(4,8,2,'accepted','2026-04-22 18:05:00','2026-04-22 14:05:24');
/*!40000 ALTER TABLE `client_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_applications`
--

DROP TABLE IF EXISTS `coach_applications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_applications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `status` enum('pending','approved','denied') DEFAULT NULL,
  `notes` text,
  `reviewed_by` int DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `reviewed_by` (`reviewed_by`),
  CONSTRAINT `coach_applications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `coach_applications_ibfk_2` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_applications`
--

LOCK TABLES `coach_applications` WRITE;
/*!40000 ALTER TABLE `coach_applications` DISABLE KEYS */;
INSERT INTO `coach_applications` VALUES (1,2,'approved','test\n',1,'2026-04-22 17:14:06','2026-04-22 17:49:43');
/*!40000 ALTER TABLE `coach_applications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_availability`
--

DROP TABLE IF EXISTS `coach_availability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_availability` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coach_id` int NOT NULL,
  `day_of_week` int DEFAULT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  PRIMARY KEY (`id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `coach_availability_ibfk_1` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_availability`
--

LOCK TABLES `coach_availability` WRITE;
/*!40000 ALTER TABLE `coach_availability` DISABLE KEYS */;
/*!40000 ALTER TABLE `coach_availability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_pricing`
--

DROP TABLE IF EXISTS `coach_pricing`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_pricing` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coach_id` int NOT NULL,
  `session_type` varchar(50) DEFAULT NULL,
  `price` decimal(10,2) NOT NULL,
  `currency` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `coach_pricing_ibfk_1` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_pricing`
--

LOCK TABLES `coach_pricing` WRITE;
/*!40000 ALTER TABLE `coach_pricing` DISABLE KEYS */;
INSERT INTO `coach_pricing` VALUES (3,3,'1-on-1 Session',45.00,'USD'),(4,3,'Group Session',20.00,'USD'),(5,4,'1-on-1 Session',60.00,'USD'),(6,4,'Monthly Package',220.00,'USD'),(7,5,'1-on-1 Session',55.00,'USD'),(8,5,'Group Class',18.00,'USD'),(9,6,'1-on-1 Session',65.00,'USD'),(10,6,'Monthly Package',250.00,'USD'),(11,2,'1-on-1 Session',50.00,'USD'),(12,2,'Monthly Package',180.00,'USD');
/*!40000 ALTER TABLE `coach_pricing` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_relationships`
--

DROP TABLE IF EXISTS `coach_relationships`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_relationships` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `status` enum('active','ended') DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `coach_relationships_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `coach_relationships_ibfk_2` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_relationships`
--

LOCK TABLES `coach_relationships` WRITE;
/*!40000 ALTER TABLE `coach_relationships` DISABLE KEYS */;
INSERT INTO `coach_relationships` VALUES (1,7,2,'ended','2026-04-22 17:11:24',NULL),(2,8,2,'ended','2026-04-22 17:50:51',NULL),(3,8,2,'ended','2026-04-22 17:56:43',NULL),(4,8,2,'active','2026-04-22 18:05:24',NULL);
/*!40000 ALTER TABLE `coach_relationships` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_specializations`
--

DROP TABLE IF EXISTS `coach_specializations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_specializations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `coach_id` int NOT NULL,
  `specialization_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `coach_id` (`coach_id`),
  KEY `specialization_id` (`specialization_id`),
  CONSTRAINT `coach_specializations_ibfk_1` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `coach_specializations_ibfk_2` FOREIGN KEY (`specialization_id`) REFERENCES `specializations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_specializations`
--

LOCK TABLES `coach_specializations` WRITE;
/*!40000 ALTER TABLE `coach_specializations` DISABLE KEYS */;
INSERT INTO `coach_specializations` VALUES (2,3,2),(3,4,3),(4,4,4),(5,5,5),(6,6,6),(7,2,1);
/*!40000 ALTER TABLE `coach_specializations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_surveys`
--

DROP TABLE IF EXISTS `coach_surveys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_surveys` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `experience_years` int DEFAULT NULL,
  `certifications` text,
  `bio` text,
  `specialization_notes` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `coach_surveys_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_surveys`
--

LOCK TABLES `coach_surveys` WRITE;
/*!40000 ALTER TABLE `coach_surveys` DISABLE KEYS */;
INSERT INTO `coach_surveys` VALUES (1,2,5,'Test Certification A','Test coach bio for coach #1.','General fitness'),(2,3,3,'Test Certification B','Test coach bio for coach #2.','Cardio and endurance'),(3,4,7,'Test Certification C','Test coach bio for coach #3.','Weight loss programs'),(4,5,10,'Test Certification D','Test coach bio for coach #4.','Yoga and mobility'),(5,6,4,'Test Certification E','Test coach bio for coach #5.','Muscle building');
/*!40000 ALTER TABLE `coach_surveys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_metrics`
--

DROP TABLE IF EXISTS `daily_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_metrics` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `log_date` date NOT NULL,
  `steps` int DEFAULT NULL,
  `calories_burned` int DEFAULT NULL,
  `water_intake_ml` int DEFAULT NULL,
  `notes` text,
  `created_at` datetime DEFAULT NULL,
  `date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `daily_metrics_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_metrics`
--

LOCK TABLES `daily_metrics` WRITE;
/*!40000 ALTER TABLE `daily_metrics` DISABLE KEYS */;
/*!40000 ALTER TABLE `daily_metrics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercise_logs`
--

DROP TABLE IF EXISTS `exercise_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercise_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `workout_log_id` int NOT NULL,
  `exercise_id` int NOT NULL,
  `sets_completed` int DEFAULT NULL,
  `reps_completed` varchar(50) DEFAULT NULL,
  `weight_used` varchar(50) DEFAULT NULL,
  `duration_minutes` int DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `workout_log_id` (`workout_log_id`),
  KEY `exercise_id` (`exercise_id`),
  CONSTRAINT `exercise_logs_ibfk_1` FOREIGN KEY (`workout_log_id`) REFERENCES `workout_logs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `exercise_logs_ibfk_2` FOREIGN KEY (`exercise_id`) REFERENCES `exercises` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercise_logs`
--

LOCK TABLES `exercise_logs` WRITE;
/*!40000 ALTER TABLE `exercise_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `exercise_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercises`
--

DROP TABLE IF EXISTS `exercises`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercises` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` text,
  `category` enum('cardio','strength','flexibility','balance','sports') DEFAULT NULL,
  `muscle_group` varchar(100) DEFAULT NULL,
  `equipment` varchar(100) DEFAULT NULL,
  `difficulty` enum('beginner','intermediate','advanced') DEFAULT NULL,
  `video_url` varchar(255) DEFAULT NULL,
  `instructions` text,
  `created_by` int DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `calories` int DEFAULT NULL,
  `default_duration_minutes` int DEFAULT NULL,
  `is_library_workout` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `exercises_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercises`
--

LOCK TABLES `exercises` WRITE;
/*!40000 ALTER TABLE `exercises` DISABLE KEYS */;
INSERT INTO `exercises` VALUES (1,'Morning Jog','Easy outdoor jog at a conversational pace to build aerobic base.','cardio','legs','none','beginner',NULL,'Warm up with 5 minutes of brisk walking, then jog at a steady, comfortable pace.',NULL,1,280,30,1,'2026-04-22 14:52:17'),(2,'HIIT Cardio Blast','High-intensity interval training alternating all-out effort and rest.','cardio','full-body','bodyweight','advanced',NULL,'30 seconds max-effort, 30 seconds rest. Repeat for 20 minutes.',NULL,1,350,20,1,'2026-04-22 14:52:17'),(3,'Indoor Cycling','Steady-state stationary bike ride with moderate resistance.','cardio','legs','stationary bike','beginner',NULL,'Maintain cadence of 80-90 RPM at moderate resistance.',NULL,1,300,45,1,'2026-04-22 14:52:17'),(4,'Upper Body Strength','Classic push/pull routine focused on the chest, back, and arms.','strength','upper-body','dumbbells','intermediate',NULL,'3 sets of: bench press, rows, shoulder press, curls, tricep extensions.',NULL,1,220,40,1,'2026-04-22 14:52:17'),(5,'Leg Day','Compound lower-body strength session targeting quads, hamstrings, and glutes.','strength','legs','barbell','intermediate',NULL,'Squats, Romanian deadlifts, lunges, and calf raises. 4 sets each.',NULL,1,320,50,1,'2026-04-22 14:52:17'),(6,'Core Crusher','Focused abdominal and core stability circuit.','strength','core','bodyweight','beginner',NULL,'Plank, mountain climbers, bicycle crunches, leg raises. 3 rounds.',NULL,1,150,20,1,'2026-04-22 14:52:17'),(7,'Full-Body Bodyweight','No-equipment circuit hitting every major muscle group.','strength','full-body','bodyweight','beginner',NULL,'Push-ups, squats, lunges, plank, burpees. 4 rounds.',NULL,1,260,30,1,'2026-04-22 14:52:17'),(8,'Vinyasa Yoga Flow','Dynamic yoga sequence for flexibility and mobility.','flexibility','full-body','yoga mat','beginner',NULL,'Flow through sun salutations, warrior poses, and deep stretches.',NULL,1,180,45,1,'2026-04-22 14:52:17'),(9,'Mobility & Stretch','Slow-paced mobility routine to release tension and improve range of motion.','flexibility','full-body','yoga mat','beginner',NULL,'Hip openers, hamstring stretches, shoulder circles, cat-cow.',NULL,1,90,20,1,'2026-04-22 14:52:17'),(10,'Balance Training','Balance and stability drills for improved coordination.','balance','legs','none','beginner',NULL,'Single-leg stands, heel-to-toe walks, tree pose. Hold each for 30 seconds.',NULL,1,110,20,1,'2026-04-22 14:52:17'),(11,'Pickup Basketball','Casual basketball game — sprint, jump, pivot, and shoot.','sports','full-body','basketball','intermediate',NULL,'Play a full-court pickup game with friends at a moderate pace.',NULL,1,500,60,1,'2026-04-22 14:52:17'),(12,'Pool Swim','Freestyle lap swimming for low-impact full-body cardio.','cardio','full-body','pool','intermediate',NULL,'Warm up 200m easy, then 20 x 50m with 15s rest.',NULL,1,400,40,1,'2026-04-22 14:52:17');
/*!40000 ALTER TABLE `exercises` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `fitness_surveys`
--

DROP TABLE IF EXISTS `fitness_surveys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_surveys` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `weight` decimal(5,2) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `fitness_level` enum('beginner','intermediate','advanced') DEFAULT NULL,
  `goals` text,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fitness_surveys_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fitness_surveys`
--

LOCK TABLES `fitness_surveys` WRITE;
/*!40000 ALTER TABLE `fitness_surveys` DISABLE KEYS */;
/*!40000 ALTER TABLE `fitness_surveys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meal_logs`
--

DROP TABLE IF EXISTS `meal_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meal_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `date` date NOT NULL,
  `meal_type` enum('breakfast','lunch','dinner','snack') DEFAULT NULL,
  `food_items` text,
  `calories` int DEFAULT NULL,
  `protein_g` decimal(6,2) DEFAULT NULL,
  `carbs_g` decimal(6,2) DEFAULT NULL,
  `fat_g` decimal(6,2) DEFAULT NULL,
  `notes` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `meal_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meal_logs`
--

LOCK TABLES `meal_logs` WRITE;
/*!40000 ALTER TABLE `meal_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `meal_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meal_plans`
--

DROP TABLE IF EXISTS `meal_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meal_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `notes` text,
  `created_at` datetime DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `meal_plans_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meal_plans`
--

LOCK TABLES `meal_plans` WRITE;
/*!40000 ALTER TABLE `meal_plans` DISABLE KEYS */;
/*!40000 ALTER TABLE `meal_plans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `moderation_reports`
--

DROP TABLE IF EXISTS `moderation_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `moderation_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `report_type` enum('coach','chat') NOT NULL,
  `reporter_id` int NOT NULL,
  `reported_user_id` int DEFAULT NULL,
  `relationship_id` int DEFAULT NULL,
  `reason` varchar(255) NOT NULL,
  `details` text,
  `status` enum('open','reviewed','resolved','dismissed') DEFAULT NULL,
  `reviewed_by` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `reporter_id` (`reporter_id`),
  KEY `reported_user_id` (`reported_user_id`),
  KEY `relationship_id` (`relationship_id`),
  KEY `reviewed_by` (`reviewed_by`),
  CONSTRAINT `moderation_reports_ibfk_1` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `moderation_reports_ibfk_2` FOREIGN KEY (`reported_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `moderation_reports_ibfk_3` FOREIGN KEY (`relationship_id`) REFERENCES `coach_relationships` (`id`) ON DELETE CASCADE,
  CONSTRAINT `moderation_reports_ibfk_4` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `moderation_reports`
--

LOCK TABLES `moderation_reports` WRITE;
/*!40000 ALTER TABLE `moderation_reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `moderation_reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  `message` text,
  `read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment_records`
--

DROP TABLE IF EXISTS `payment_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `payer_id` int NOT NULL,
  `coach_id` int DEFAULT NULL,
  `payment_reference` varchar(100) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `currency` varchar(3) DEFAULT NULL,
  `status` varchar(30) DEFAULT NULL,
  `metadata_json` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `payment_reference` (`payment_reference`),
  KEY `payer_id` (`payer_id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `payment_records_ibfk_1` FOREIGN KEY (`payer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `payment_records_ibfk_2` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment_records`
--

LOCK TABLES `payment_records` WRITE;
/*!40000 ALTER TABLE `payment_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `payment_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plan_exercises`
--

DROP TABLE IF EXISTS `plan_exercises`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plan_exercises` (
  `id` int NOT NULL AUTO_INCREMENT,
  `workout_day_id` int NOT NULL,
  `exercise_id` int NOT NULL,
  `order` int DEFAULT NULL,
  `sets` int DEFAULT NULL,
  `reps` varchar(50) DEFAULT NULL,
  `duration_minutes` int DEFAULT NULL,
  `rest_seconds` int DEFAULT NULL,
  `weight` varchar(50) DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `workout_day_id` (`workout_day_id`),
  KEY `exercise_id` (`exercise_id`),
  CONSTRAINT `plan_exercises_ibfk_1` FOREIGN KEY (`workout_day_id`) REFERENCES `workout_days` (`id`) ON DELETE CASCADE,
  CONSTRAINT `plan_exercises_ibfk_2` FOREIGN KEY (`exercise_id`) REFERENCES `exercises` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plan_exercises`
--

LOCK TABLES `plan_exercises` WRITE;
/*!40000 ALTER TABLE `plan_exercises` DISABLE KEYS */;
INSERT INTO `plan_exercises` VALUES (1,1,2,NULL,NULL,NULL,20,NULL,NULL,NULL),(2,2,1,NULL,3,'10',NULL,60,'bodyweight','');
/*!40000 ALTER TABLE `plan_exercises` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reviews`
--

DROP TABLE IF EXISTS `reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `rating` int NOT NULL,
  `comment` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  KEY `coach_id` (`coach_id`),
  CONSTRAINT `reviews_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `reviews_ibfk_2` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reviews`
--

LOCK TABLES `reviews` WRITE;
/*!40000 ALTER TABLE `reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_change_requests`
--

DROP TABLE IF EXISTS `role_change_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_change_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `current_role` varchar(20) DEFAULT NULL,
  `requested_role` enum('coach','both') NOT NULL,
  `reason` text,
  `status` enum('pending','approved','rejected') NOT NULL,
  `admin_notes` text,
  `created_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `reviewed_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `reviewed_by` (`reviewed_by`),
  KEY `ix_role_change_requests_status` (`status`),
  KEY `ix_role_change_requests_user_id` (`user_id`),
  CONSTRAINT `role_change_requests_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `role_change_requests_ibfk_2` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_change_requests`
--

LOCK TABLES `role_change_requests` WRITE;
/*!40000 ALTER TABLE `role_change_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `role_change_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `specializations`
--

DROP TABLE IF EXISTS `specializations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specializations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specializations`
--

LOCK TABLES `specializations` WRITE;
/*!40000 ALTER TABLE `specializations` DISABLE KEYS */;
INSERT INTO `specializations` VALUES (1,'Strength Training','fitness'),(2,'Cardio Training','fitness'),(3,'Weight Loss','fitness'),(4,'Nutrition Coaching','fitness'),(5,'Yoga & Flexibility','fitness'),(6,'Muscle Gain','fitness');
/*!40000 ALTER TABLE `specializations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_profiles`
--

DROP TABLE IF EXISTS `user_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_profiles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `profile_picture` varchar(255) DEFAULT NULL,
  `bio` text,
  `phone` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_profiles`
--

LOCK TABLES `user_profiles` WRITE;
/*!40000 ALTER TABLE `user_profiles` DISABLE KEYS */;
INSERT INTO `user_profiles` VALUES (1,1,'Test','Admin',NULL,NULL,NULL),(2,2,'Test','CoachOne',NULL,'Generic test coach #1 for QA and development.','+1-555-1001'),(3,3,'Test','CoachTwo',NULL,'Generic test coach #2 for QA and development.','+1-555-1002'),(4,4,'Test','CoachThree',NULL,'Generic test coach #3 for QA and development.','+1-555-1003'),(5,5,'Test','CoachFour',NULL,'Generic test coach #4 for QA and development.','+1-555-1004'),(6,6,'Test','CoachFive',NULL,'Generic test coach #5 for QA and development.','+1-555-1005'),(7,7,'Test','ClientOne',NULL,'Generic test client #1 for QA and development.','+1-555-2001'),(8,8,'Test','ClientTwo',NULL,'Generic test client #2 for QA and development.','+1-555-2002'),(9,9,'Test','ClientThree',NULL,'Generic test client #3 for QA and development.','+1-555-2003'),(10,10,'Test','ClientFour',NULL,'Generic test client #4 for QA and development.','+1-555-2004'),(11,11,'Test','ClientFive',NULL,'Generic test client #5 for QA and development.','+1-555-2005');
/*!40000 ALTER TABLE `user_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('client','coach','both','admin') DEFAULT NULL,
  `status` enum('active','disabled') DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin@test.fit','scrypt:32768:8:1$AzaHvsJTh06ofHH8$49bc9c4e3d39278b362a83912b99e786ed1d974dcde0317b92fc98ff1a589e97503cd5683ad07d1d717b66c62de713beada5936872c43c054c77339b70cdc236','admin','active','2026-04-22 14:35:25','2026-04-22 14:35:25'),(2,'coach1@test.fit','scrypt:32768:8:1$5g61iLfjbgfVHsGi$3a2e851cfce67673b2a7b2dd76321e59e44c4d54792dbe99a81cea91eda2baa5a7d0106f3a9f3648a1a35c292ada0e3397259762ec4eb45de558f80e66517f91','coach','active','2026-04-22 14:35:25','2026-04-22 14:35:25'),(3,'coach2@test.fit','scrypt:32768:8:1$1QCmivvERVl7hKAl$65430bc811218b0ea71f87b215e5aa7d4a1199ce914d49cc1cba84e2b8145a419daad585d6bbd2107e07456ebf87f9f5539bc1e0141f90a3207449f2c379f871','coach','active','2026-04-22 14:35:25','2026-04-22 14:35:25'),(4,'coach3@test.fit','scrypt:32768:8:1$V32EKkfW7K6Hsc2K$951cbd2ec9190beff8d0a1c101e4ca228044d998acf661bffe7c9701e2787085366013bdef920d0ad7b30325d97f99b871805be0e7c94d1d1eaefeb6c48a4d9d','coach','active','2026-04-22 14:35:25','2026-04-22 14:35:25'),(5,'coach4@test.fit','scrypt:32768:8:1$9J0WYIzn3KGSvpfk$e53955893752a050776c73425911f0067245f82e5e24af17d7667d4f2a59ea87db45c50cdbcfc3f802b7cc156f698f2cec23f572edaf7f0c1b70206e856ee63e','coach','active','2026-04-22 14:35:25','2026-04-22 14:35:25'),(6,'coach5@test.fit','scrypt:32768:8:1$NNKr4Xcnnn94jyqS$808576b34f71cae40d32eeb870c45ed2f92db8ce975fd2d55f4c74c4f6d3c1f36ba86547e2db0c397fd510d2e8f6ba51d9dccf45c8f8532b15d0bf0050f1f0e9','coach','active','2026-04-22 14:35:26','2026-04-22 14:35:26'),(7,'client1@test.fit','scrypt:32768:8:1$5zaAVqPpcKN5QnQR$7f018c819bb8fa8f16a0823188a51ca945eee939f975a5563e2a021555df2f477bc5baa8d2e7c093eb68bdb62f85e4d25bd1ea766676af94fa9aa98eb9ed402b','client','active','2026-04-22 14:35:26','2026-04-22 14:35:26'),(8,'client2@test.fit','scrypt:32768:8:1$rpudWnux5xuffOGf$8117b44b968e20be27d6cdb26c7f67036defde532dd54f27c12f0aa11a5c667fc622884a2494e3cc0fde3cfb9e363a48b99d1c9f41676425a9ac7225ef8b68a9','client','active','2026-04-22 14:35:26','2026-04-22 14:35:26'),(9,'client3@test.fit','scrypt:32768:8:1$bud4qnankBFYf3C4$5cdc18747ab772a06660efb21bfa7efe77119faec3e52379f14c2511eb168e1f55887bbb15dd9f18231205bcf4dfaddfede99e1c0f64b68ef686ef363fb5290f','client','active','2026-04-22 14:35:26','2026-04-22 14:35:26'),(10,'client4@test.fit','scrypt:32768:8:1$ldWLM2RIcnCMCeRL$f79af5f517e00e0f70a30ff4f760616b219fc1fa600bd5489c0057b9c293a2bf610257209e60a3e06ec980d2cc83784995b728ab87eca462325db94fc57df3da','client','active','2026-04-22 14:35:26','2026-04-22 14:35:26'),(11,'client5@test.fit','scrypt:32768:8:1$Kpk2LzgXg8yi6KLr$71931d7d557fa8f90d9fae7e1c63041738557f5b5c52ba99854216e44f6cb72e6580332ae45c900ee72c32f42bd9840ba717cb9ed8cc7ec91f412f8693af1942','client','active','2026-04-22 14:35:26','2026-04-22 14:35:26');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wellness_logs`
--

DROP TABLE IF EXISTS `wellness_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `wellness_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `date` date NOT NULL,
  `mood` enum('excellent','good','okay','poor','terrible') DEFAULT NULL,
  `energy_level` int DEFAULT NULL,
  `stress_level` int DEFAULT NULL,
  `sleep_hours` decimal(4,2) DEFAULT NULL,
  `sleep_quality` enum('excellent','good','fair','poor') DEFAULT NULL,
  `water_intake_ml` int DEFAULT NULL,
  `notes` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `wellness_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wellness_logs`
--

LOCK TABLES `wellness_logs` WRITE;
/*!40000 ALTER TABLE `wellness_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `wellness_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_days`
--

DROP TABLE IF EXISTS `workout_days`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_days` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plan_id` int NOT NULL,
  `name` varchar(200) NOT NULL,
  `day_number` int DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`id`),
  KEY `plan_id` (`plan_id`),
  CONSTRAINT `workout_days_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `workout_plans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_days`
--

LOCK TABLES `workout_days` WRITE;
/*!40000 ALTER TABLE `workout_days` DISABLE KEYS */;
INSERT INTO `workout_days` VALUES (1,1,'Day 1',1,NULL),(2,2,'Day 1',1,'');
/*!40000 ALTER TABLE `workout_days` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_logs`
--

DROP TABLE IF EXISTS `workout_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `plan_id` int DEFAULT NULL,
  `workout_day_id` int DEFAULT NULL,
  `library_exercise_id` int DEFAULT NULL,
  `workout_name` varchar(200) DEFAULT NULL,
  `calories_burned` int DEFAULT NULL,
  `exercise_type` varchar(50) DEFAULT NULL,
  `muscle_group` varchar(100) DEFAULT NULL,
  `date` date NOT NULL,
  `duration_minutes` int DEFAULT NULL,
  `notes` text,
  `rating` int DEFAULT NULL,
  `completed` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  KEY `plan_id` (`plan_id`),
  KEY `workout_day_id` (`workout_day_id`),
  KEY `library_exercise_id` (`library_exercise_id`),
  CONSTRAINT `workout_logs_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workout_logs_ibfk_2` FOREIGN KEY (`plan_id`) REFERENCES `workout_plans` (`id`) ON DELETE SET NULL,
  CONSTRAINT `workout_logs_ibfk_3` FOREIGN KEY (`workout_day_id`) REFERENCES `workout_days` (`id`) ON DELETE SET NULL,
  CONSTRAINT `workout_logs_ibfk_4` FOREIGN KEY (`library_exercise_id`) REFERENCES `exercises` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_logs`
--

LOCK TABLES `workout_logs` WRITE;
/*!40000 ALTER TABLE `workout_logs` DISABLE KEYS */;
INSERT INTO `workout_logs` VALUES (1,7,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2026-04-22',NULL,'',4,1,'2026-04-22 14:41:05'),(2,7,NULL,NULL,1,'Morning Jog',280,'cardio','legs','2026-04-22',30,NULL,3,1,'2026-04-22 17:10:26');
/*!40000 ALTER TABLE `workout_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_plan_assignments`
--

DROP TABLE IF EXISTS `workout_plan_assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_plan_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `plan_id` int NOT NULL,
  `workout_day_id` int DEFAULT NULL,
  `assigned_date` date NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `plan_id` (`plan_id`),
  KEY `workout_day_id` (`workout_day_id`),
  CONSTRAINT `workout_plan_assignments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workout_plan_assignments_ibfk_2` FOREIGN KEY (`plan_id`) REFERENCES `workout_plans` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workout_plan_assignments_ibfk_3` FOREIGN KEY (`workout_day_id`) REFERENCES `workout_days` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_plan_assignments`
--

LOCK TABLES `workout_plan_assignments` WRITE;
/*!40000 ALTER TABLE `workout_plan_assignments` DISABLE KEYS */;
/*!40000 ALTER TABLE `workout_plan_assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_plan_metadata`
--

DROP TABLE IF EXISTS `workout_plan_metadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_plan_metadata` (
  `id` int NOT NULL AUTO_INCREMENT,
  `plan_id` int NOT NULL,
  `goal` varchar(100) DEFAULT NULL,
  `difficulty` varchar(50) DEFAULT NULL,
  `plan_type` varchar(50) DEFAULT NULL,
  `duration_weeks` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `plan_id` (`plan_id`),
  CONSTRAINT `workout_plan_metadata_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `workout_plans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_plan_metadata`
--

LOCK TABLES `workout_plan_metadata` WRITE;
/*!40000 ALTER TABLE `workout_plan_metadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `workout_plan_metadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_plans`
--

DROP TABLE IF EXISTS `workout_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` text,
  `coach_id` int DEFAULT NULL,
  `client_id` int NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `status` enum('active','completed','archived') DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `coach_id` (`coach_id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `workout_plans_ibfk_1` FOREIGN KEY (`coach_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workout_plans_ibfk_2` FOREIGN KEY (`client_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_plans`
--

LOCK TABLES `workout_plans` WRITE;
/*!40000 ALTER TABLE `workout_plans` DISABLE KEYS */;
INSERT INTO `workout_plans` VALUES (1,'Test plan',NULL,NULL,7,NULL,NULL,'active','2026-04-22 17:10:43','2026-04-22 17:10:43'),(2,'test plan','test goal',2,8,'2026-04-23','2026-04-29','active','2026-04-22 18:07:34','2026-04-22 18:07:34');
/*!40000 ALTER TABLE `workout_plans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_templates`
--

DROP TABLE IF EXISTS `workout_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `description` text,
  `goal` varchar(100) DEFAULT NULL,
  `difficulty` varchar(50) DEFAULT NULL,
  `plan_type` varchar(50) DEFAULT NULL,
  `duration_weeks` int DEFAULT NULL,
  `template_data` text NOT NULL,
  `created_by` int DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `approved` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `workout_templates_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_templates`
--

LOCK TABLES `workout_templates` WRITE;
/*!40000 ALTER TABLE `workout_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `workout_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'fitness_app'
--

--
-- Dumping routines for database 'fitness_app'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;