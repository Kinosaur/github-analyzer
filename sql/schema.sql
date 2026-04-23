-- 1. Raw Ingestion Tables

CREATE TABLE IF NOT EXISTS repos (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    description TEXT,
    html_url VARCHAR(255),
    is_private BOOLEAN,
    is_fork BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    pushed_at TIMESTAMP,
    size_kb INT,
    stargazers_count INT,
    forks_count INT,
    open_issues_count INT,
    primary_language VARCHAR(100),
    topics TEXT[]
);

CREATE TABLE IF NOT EXISTS repo_languages (
    repo_id BIGINT REFERENCES repos(id) ON DELETE CASCADE,
    language VARCHAR(100) NOT NULL,
    byte_count INT,
    PRIMARY KEY (repo_id, language)
);

CREATE TABLE IF NOT EXISTS commits (
    sha VARCHAR(40) PRIMARY KEY,
    repo_id BIGINT REFERENCES repos(id) ON DELETE CASCADE,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    commit_date TIMESTAMP,
    message TEXT
);

-- 2. Transformation Tables (Analytics)

CREATE TABLE IF NOT EXISTS repo_scores (
    repo_id BIGINT PRIMARY KEY REFERENCES repos(id) ON DELETE CASCADE,
    popularity_score NUMERIC(10, 2),
    activity_score NUMERIC(10, 2),
    recency_score NUMERIC(10, 2),
    overall_score NUMERIC(10, 2),
    rank INT,
    classification VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Orchestration & Logging

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    repos_processed INT DEFAULT 0,
    commits_processed INT DEFAULT 0,
    error_message TEXT
);
