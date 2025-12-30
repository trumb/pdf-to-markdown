-- PDF2MD Database Schema
-- Version: 1.0.0
-- Description: SQLite schema for token management, job tracking, and access control

-- Tokens table: Stores API tokens with bcrypt hashes
CREATE TABLE IF NOT EXISTS tokens (
    token_id TEXT PRIMARY KEY,           -- UUID
    token_hash TEXT NOT NULL,            -- bcrypt hash
    user_id TEXT NOT NULL,               -- Human-readable identifier
    role TEXT NOT NULL CHECK(role IN ('admin', 'job_manager', 'job_writer', 'job_reader')),
    created_at TEXT NOT NULL,            -- ISO 8601
    expires_at TEXT,                     -- ISO 8601 or NULL
    is_active INTEGER NOT NULL DEFAULT 1, -- Boolean
    rate_limit INTEGER NOT NULL DEFAULT 60, -- Requests per minute
    scopes TEXT,                         -- JSON array
    created_by TEXT                      -- token_id of creator (for audit)
);

-- Token usage audit trail
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    request_size_bytes INTEGER,
    response_time_ms INTEGER,
    status_code INTEGER,
    FOREIGN KEY (token_id) REFERENCES tokens(token_id)
);

-- Jobs table: PDF conversion jobs
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,             -- 10-char case-sensitive
    owner_user_id TEXT NOT NULL,
    pdf_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    result_path TEXT,                    -- Path to result markdown
    error_message TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    throttled INTEGER DEFAULT 0,         -- Boolean
    throttled_by TEXT,                   -- user_id of admin/manager
    options TEXT                         -- JSON: output format, image handling, etc.
);

-- Job access grants: Allow users to access jobs they don't own
CREATE TABLE IF NOT EXISTS job_access_grants (
    job_id TEXT NOT NULL,
    granted_to_user_id TEXT NOT NULL,
    granted_by_user_id TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    PRIMARY KEY (job_id, granted_to_user_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_tokens_role ON tokens(role);
CREATE INDEX IF NOT EXISTS idx_token_usage_token_id ON token_usage(token_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_jobs_owner ON jobs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_grants_user ON job_access_grants(granted_to_user_id);