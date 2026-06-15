-- Enable extensions on database creation.
-- The pgvector image ships the extension under the name "vector" (not "pgvector").
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- trigram search for failure text
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
