-- Enable extensions on database creation
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- trigram search for failure text
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
