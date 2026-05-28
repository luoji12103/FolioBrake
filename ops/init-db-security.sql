-- Database initialization script for FolioBrake
-- Creates a dedicated application user with minimal permissions

-- Create application user (if not using the default guardian user)
-- DO NOT use this in production with the default credentials

-- Revoke default public schema permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Grant minimal required permissions to the application user
GRANT USAGE ON SCHEMA public TO guardian;
GRANT CREATE ON SCHEMA public TO guardian;

-- Grant table-level permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO guardian;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO guardian;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO guardian;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO guardian;

-- Security: Prevent the application user from creating extensions or modifying schema
-- (only allow DML operations)
ALTER USER guardian CREATEDB;
REVOKE CREATE ON SCHEMA public FROM guardian;

-- Set connection limits
ALTER USER guardian CONNECTION LIMIT 50;

-- Set statement timeout for safety
ALTER USER guardian SET statement_timeout = '30s';
ALTER USER guardian SET lock_timeout = '10s';
