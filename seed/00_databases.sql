-- Create databases for all services
-- This script runs first (00 prefix) to ensure databases exist before services start
-- Note: PostgreSQL doesn't support IF NOT EXISTS for CREATE DATABASE, so we use DO block

DO $$
BEGIN
    -- Recommendations Service Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'recommendations_db') THEN
        CREATE DATABASE recommendations_db;
    END IF;
    
    -- Notification Service Database
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notification_db') THEN
        CREATE DATABASE notification_db;
    END IF;
END
$$;
