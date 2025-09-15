-- Initial database setup script for PostgreSQL
-- This script is used by Docker Compose for local development

-- Create the database user if it doesn't exist (Docker handles this)
-- CREATE USER IF NOT EXISTS vriddhi_user WITH PASSWORD 'vriddhi_password';

-- Grant permissions
-- GRANT ALL PRIVILEGES ON DATABASE vriddhi_db TO vriddhi_user;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Add any initial data or configuration here
-- Tables will be created by SQLAlchemy migrations

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0)
ON CONFLICT DO NOTHING;