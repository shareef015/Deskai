-- Execute through customer-controlled database provisioning, not application startup.
-- Role membership and passwords/certificates are supplied by the private deployment.
CREATE ROLE deskpilot_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
CREATE ROLE deskpilot_migrator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;

GRANT USAGE ON SCHEMA public TO deskpilot_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO deskpilot_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE deskpilot_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO deskpilot_runtime;

-- The migrator owns schema objects; runtime receives DML only and never table ownership.
REVOKE CREATE ON SCHEMA public FROM deskpilot_runtime;
REVOKE SET ON PARAMETER row_security FROM deskpilot_runtime;
