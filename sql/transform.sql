-- Ensure the repo_scores table has the new quality_score column
ALTER TABLE repo_scores ADD COLUMN IF NOT EXISTS quality_score NUMERIC(10, 2);

-- Clear existing scores to ensure a clean calculation
TRUNCATE repo_scores;

WITH commit_counts AS (
    SELECT repo_id, COUNT(*) as c_count
    FROM commits
    GROUP BY repo_id
),
repo_metrics AS (
    SELECT 
        r.id as repo_id,
        r.is_fork,
        COALESCE(c.c_count, 0) as commit_count,
        r.stargazers_count,
        r.forks_count,
        r.pushed_at,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.pushed_at))/86400.0 as days_since_push,
        r.has_readme,
        r.description,
        r.topics
    FROM repos r
    LEFT JOIN commit_counts c ON r.id = c.repo_id
),
-- Removed the strict fork filter (filtered_metrics CTE removed)
calculated_scores AS (
    SELECT
        repo_id,
        is_fork,
        -- Popularity: Zero base for 0 stars/forks.
        LEAST(100.0, LN((stargazers_count * 5 + forks_count * 10) + 1.0) * 15.0) as popularity_score,
        
        -- Activity (Recent): Multiplier so 40 recent commits maxes out the score.
        LEAST(100.0, commit_count * 2.5) as activity_score,
        
        -- Recency: True half-life math using ln(2) approx 0.693147. 365 days half-life.
        100.0 * EXP(-COALESCE(days_since_push, 9999) * 0.693147 / 365.0) as recency_score,

        -- Presentation (Quality): Safer array cardinality check for topics.
        (CASE WHEN has_readme THEN 50.0 ELSE 0.0 END) +
        (CASE WHEN description IS NOT NULL AND description != '' THEN 30.0 ELSE 0.0 END) +
        (CASE WHEN topics IS NOT NULL AND cardinality(topics) > 0 THEN 20.0 ELSE 0.0 END) as quality_score
    FROM repo_metrics
),
weighted_scores AS (
    SELECT
        repo_id,
        popularity_score,
        activity_score,
        recency_score,
        quality_score,
        -- Overall score using internship-focused weights: Recency(50) Activity(30) Popularity(10) Quality(10)
        -- Fork Penalty: Multiply final score by 0.8 if it is a fork.
        ((recency_score * 0.50) + (activity_score * 0.30) + (popularity_score * 0.10) + (quality_score * 0.10)) * (CASE WHEN is_fork THEN 0.80 ELSE 1.00 END) as overall_score
    FROM calculated_scores
)
INSERT INTO repo_scores (repo_id, popularity_score, activity_score, recency_score, quality_score, overall_score, rank, classification)
SELECT
    repo_id,
    ROUND(popularity_score::numeric, 2),
    ROUND(activity_score::numeric, 2),
    ROUND(recency_score::numeric, 2),
    ROUND(quality_score::numeric, 2),
    ROUND(overall_score::numeric, 2),
    RANK() OVER (ORDER BY overall_score DESC) as rank,
    CASE 
        WHEN recency_score > 50 AND activity_score > 10 THEN 'Active'
        WHEN recency_score > 10 THEN 'Maintenance'
        ELSE 'Archived'
    END as classification
FROM weighted_scores;
