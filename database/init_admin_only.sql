-- Init: Admin-only seed
-- Loads after schema.sql. Creates a single admin account and nothing else.
--
-- Credentials:
--   Email:    admin@fitness.app
--   Password: Admin123!

USE fitness_app;

SET @admin_password = 'scrypt:32768:8:1$cTIpAYrTzK8BOKDn$440fb77f21b5361868f680e52c8b4b7b419f86bc9599bc0561d619a9743ea893569544636015cf65201e20fe2ba9ad2d03b3c1824b2cfb6d3232abdb21e6396b';

INSERT INTO users (email, password_hash, role, status) VALUES
    ('admin@fitness.app', @admin_password, 'admin', 'active');
SET @admin_id = LAST_INSERT_ID();

INSERT INTO user_profiles (user_id, first_name, last_name) VALUES
    (@admin_id, 'Site', 'Admin');
