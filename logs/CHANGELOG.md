# Changelog

All notable changes to the GitHub Data Pipeline & Portfolio Analyzer project will be documented in this file.

## [Unreleased] - Phase 1 to 5 Completed
*Date: 2026-04-23*

### Added
- **Project Structure**: Initialized `src/`, `data/`, `logs/`, `sql/`, `dashboard/`, `tests/` directories.
- **Environment Management**: Created `.venv`, populated `.env` with GitHub API tokens and PostgreSQL credentials, and created `requirements.txt` (`requests`, `python-dotenv`, `psycopg2-binary`).
- **Storage Layer**: Designed and implemented PostgreSQL database schema (`sql/schema.sql`):
  - `repos` for core metadata.
  - `repo_languages` for tracking programming languages and byte counts.
  - `commits` for tracking commit history.
  - `repo_scores` for holding transformed rankings.
  - `pipeline_runs` for execution auditing.
- **Ingestion Layer**: Built `src/github_client.py` for API requests with pagination, automatic rate-limit sleeping, and retry mechanisms.
- **Database Connector**: Built `src/db.py` utilizing idempotent `INSERT ... ON CONFLICT DO UPDATE` commands for safe reruns.
- **Ingestion Orchestrator**: Built `src/ingest.py` to pull top 100 recent commits and populate the storage layer.
- **Data Backfill**: Created and ran `src/backfill_readmes.py` to explicitly check and store whether a repository has a `README.md` to feed into quality scoring.

### Changed
- **Transformation Layer**: Re-calibrated scoring logic (`sql/transform.sql`) to optimize for "internship/junior" role signaling, adjusting weights to:
  - Recency: 50%
  - Recent Activity (Captured): 30%
  - Presentation (Quality): 10%
  - Popularity: 10%
- **SQL Logic Fixes**: 
  - Adjusted Popularity score logarithmic scale to correctly base at `0.00` for repositories with no stars/forks.
  - Applied a `2.5x` multiplier to Recent Activity scoring so repositories with healthy captured activity (40+ recent commits) max out the score instead of being linearly punished.
  - Corrected Recency exponential decay to use true half-life math (`0.693147 / 365.0`) for a precise 365-day half-life to better represent consistency.
  - Replaced fragile PostgreSQL `array_length` checks with `cardinality()` for safely evaluating repository topics.
- **Fork Logic**: Replaced blunt filter with a soft penalty. All forks are now ranked but receive a `0.80x` multiplier penalty on their final score.
- **Terminology**: Clarified that Activity is "Recent Activity (Captured)" and Quality is actually "Presentation" to better reflect the engineering signal.

### Fixed
- Fixed an issue where the `has_readme` data was missing from the initial GitHub `/user/repos` API payload by adding a new schema column and backfilling.
