-- Seed data for users and authentication
-- This file is automatically executed when Postgres container starts

-- Insert test users (passwords are bcrypt hashed: "password123")
INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440000', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'Admin User', true, true, NOW(), NOW()),
    ('550e8400-e29b-41d4-a716-446655440001', 'user@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'Test User', true, false, NOW(), NOW()),
    ('550e8400-e29b-41d4-a716-446655440002', 'advisor@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'Advisor User', true, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

