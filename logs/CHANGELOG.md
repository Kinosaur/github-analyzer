# Changelog: GitHub Portfolio Analyzer

## [v1.0.0] - Phase 1 to 7 Completion
### Added
- **Ingestion Layer:** Custom `GitHubClient` handling pagination and secondary rate limits. Idempotent PostgreSQL UPSERT architecture using `DatabaseConnector`.
- **Data Enrichment:** Backfill script to capture README presence, powering the "Presentation Score".
- **Transformation Layer:** Fully objective, mathematical scoring engine in `transform.sql`.
  - Recency formula uses true exponential decay (`ln(2)`) with a 365-day half-life.
  - Fork penalty implemented as a soft multiplier instead of binary exclusion.
- **Analytics Layer:** Created `sql/analytics_views.sql` to strictly separate immutable data engineering math from subjective product rules.
  - `v_portfolio_scores`: Joins base scores with project multipliers.
  - `v_insights`: Uses `PERCENT_RANK()` for dynamically robust "Hidden Gem" and "Needs Attention" thresholds.
- **UX Layer (Streamlit):** Implemented "Progressive Disclosure" architecture in `dashboard/app.py`.
  - *Layer 1 (Recruiter View):* Clean leaderboard, categorized recency ("Active within last month"), and top recommendations with human-readable reasoning.
  - *Layer 2 (Narrative Explainability):* Auto-expanding row details converting raw math into "Strengths/Weaknesses".
  - *Layer 3 (Engineering Deep-Dive):* Expandable raw metric breakdown (Recency: 98, Activity: 72) for technical reviewers.

### Changed
- Refactored dashboard from a "debug panel" to a "portfolio product".
- Moved manual classifications (`system` / `practice`) directly into the `repos` table as a temporary measure.

---

## [v2.0.0-draft] - The Curation Layer Shift
*Design documentation finalized; implementation pending.*
- **Pivot:** Shifting from a hardcoded personal script to a General-Purpose Data Tool.
- **Architecture:** Decided to introduce a `repo_overrides` table to separate immutable system data from human curation.
- **Upcoming:** Adding an "Edit Mode" in Streamlit to manually override project classifications and input external contributions without breaking the data pipeline.
