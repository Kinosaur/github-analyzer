-- 1. Subjective Logic Layer (Portfolio Scores)
-- Applies the project_type multiplier to the objective base score
CREATE OR REPLACE VIEW v_portfolio_scores AS
SELECT 
    rs.repo_id,
    r.name,
    r.project_type,
    rs.overall_score as base_score,
    CASE 
        WHEN r.project_type = 'system' THEN 1.10
        WHEN r.project_type = 'practice' THEN 0.85
        ELSE 1.00
    END as adjustment_multiplier,
    (rs.overall_score * 
        CASE 
            WHEN r.project_type = 'system' THEN 1.10
            WHEN r.project_type = 'practice' THEN 0.85
            ELSE 1.00
        END
    ) as final_score,
    rs.recency_score,
    rs.activity_score,
    rs.quality_score as presentation_score,
    rs.popularity_score,
    r.stargazers_count,
    r.forks_count,
    rs.classification as activity_classification
FROM repo_scores rs
JOIN repos r ON rs.repo_id = r.id;

-- 2. Top Repositories View (Filtered & Sorted for Dashboard)
CREATE OR REPLACE VIEW v_top_repos AS
SELECT 
    RANK() OVER (ORDER BY final_score DESC) as rank,
    *
FROM v_portfolio_scores
ORDER BY final_score DESC
LIMIT 10;

-- 3. Debug / Explainability View (Full Transparency)
CREATE OR REPLACE VIEW v_repo_debug AS
SELECT 
    ps.name,
    ps.project_type,
    ps.base_score,
    ps.adjustment_multiplier,
    ps.final_score,
    ps.recency_score,
    ps.activity_score,
    ps.presentation_score,
    ps.popularity_score,
    r.stargazers_count,
    r.forks_count,
    (SELECT COUNT(*) FROM commits WHERE repo_id = r.id) as captured_commits,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.pushed_at))/86400.0 as days_since_push
FROM v_portfolio_scores ps
JOIN repos r ON r.id = ps.repo_id;

-- 4. Insights View (Percentile Based)
CREATE OR REPLACE VIEW v_insights AS
WITH percentiles AS (
    SELECT 
        name,
        final_score,
        project_type,
        PERCENT_RANK() OVER (ORDER BY popularity_score) as pop_pct,
        PERCENT_RANK() OVER (ORDER BY activity_score) as act_pct,
        PERCENT_RANK() OVER (ORDER BY presentation_score) as pres_pct,
        PERCENT_RANK() OVER (ORDER BY recency_score) as rec_pct
    FROM v_portfolio_scores
)
SELECT 
    name,
    CASE 
        WHEN pop_pct <= 0.40 AND act_pct >= 0.70 AND pres_pct >= 0.70 THEN 'Hidden Gem'
        WHEN rec_pct <= 0.40 AND pres_pct >= 0.80 THEN 'Stale but Golden'
        WHEN project_type = 'practice' THEN 'Tutorial / Practice'
        ELSE 'Standard'
    END as insight_tag
FROM percentiles;

-- 5. Language Summary
CREATE OR REPLACE VIEW v_language_summary AS
SELECT 
    l.language,
    SUM(l.byte_count) as total_bytes,
    COUNT(DISTINCT l.repo_id) as repo_count
FROM repo_languages l
GROUP BY l.language
ORDER BY total_bytes DESC;
