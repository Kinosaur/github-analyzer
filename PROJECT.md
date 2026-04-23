# GitHub Data Pipeline & Portfolio Analyzer

**Step-by-Step Build Plan (No Code, Execution-Focused)**

---

## 0. Goal (Read This First)

You are not building a script.
You are building a **data engineering project**:

> A reproducible pipeline that ingests, stores, transforms, and analyzes GitHub data using PostgreSQL.

If at any point you drift into “just making it work,” stop and come back to **pipeline thinking**.

---

## 1. Project Initialization

### 1.1 Create project structure

Create a clean root folder:

```
github-data-pipeline/
```

Inside:

```
├── .venv/
├── src/
├── data/
├── logs/
├── sql/
├── dashboard/
├── tests/
├── .env
├── requirements.txt
├── README.md
```

---

### 1.2 Setup virtual environment

* Create `.venv`
* Activate it
* Install core dependencies (mentally note categories, don’t rush to install everything)

Categories:

* HTTP client (API calls)
* PostgreSQL connector
* environment variable loader
* optional: scheduler / dashboard

---

### 1.3 Environment variables

Create `.env` file:

```
GITHUB_TOKEN=your_token
DB_NAME=github_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 2. PostgreSQL Setup

### 2.1 Create database

Database name:

```
github_db
```

Owner:

```
postgres
```

---

### 2.2 Design schema (before writing any logic)

Create SQL files in `/sql` folder.

#### Core tables:

### repos

* id (primary key)
* name
* description
* stars
* forks
* language
* created_at
* updated_at

---

### commits (aggregated)

* repo_id (foreign key)
* commit_count
* last_commit_date

---

### languages

* repo_id
* language
* percentage

---

### pipeline_runs (important signal)

* run_id
* run_timestamp
* status (success/fail)

---

### 2.3 Apply schema

* Execute SQL manually (psql or GUI)
* Verify tables exist
* Insert 1 test row manually to confirm connection later

---

## 3. Ingestion Layer (Data Collection)

### 3.1 Define scope

Start with:

* your own GitHub username

Later:

* multiple users

---

### 3.2 API understanding

You must handle:

* pagination
* rate limits
* authentication

Endpoints to conceptually use:

* user repos
* repo commits
* repo languages

---

### 3.3 Build ingestion flow (logic only)

Pipeline step:

```
1. Request repos
2. Loop through each repo
3. Extract metadata
4. Fetch additional details (commits, languages)
5. Normalize data
```

---

### 3.4 Data validation mindset

Before inserting:

* check nulls
* check duplicates
* enforce consistent types

---

## 4. Storage Layer (Critical Step)

### 4.1 Insert strategy

Do NOT blindly insert.

Decide:

* overwrite (simple)
  OR
* incremental (better)

Start with:

> overwrite per run (simpler)

---

### 4.2 Data flow

```
API → cleaned data → PostgreSQL tables
```

---

### 4.3 Logging

Every run should:

* print progress
* store pipeline_runs record

---

## 5. Transformation Layer (Your Core Value)

This is where your project becomes “data engineering.”

---

### 5.1 Define metrics

You are NOT just storing data.

Compute:

* popularity_score
* activity_score
* recency_score
* overall_score

---

### 5.2 Transformation logic

Create a mental separation:

```
raw data → transformed data
```

Options:

* SQL transformations (preferred)
* or Python processing

---

### 5.3 Example outputs

For each repo:

* rank
* score breakdown
* classification (active / inactive)

---

### 5.4 Store results

Create a new table:

### repo_scores

* repo_id
* score
* rank
* calculated_at

---

## 6. Pipeline Orchestration

### 6.1 Define pipeline stages

```
1. ingestion
2. storage
3. transformation
4. analytics output
```

---

### 6.2 Execution strategy

Start simple:

* single script that runs all steps in order

Then improve:

* scheduled execution (daily)

---

### 6.3 Idempotency (important concept)

Running pipeline multiple times should:

* not duplicate data
* not break system

---

## 7. Analytics Layer

### 7.1 Define questions your system answers

* What are my top 5 projects?
* Which repos are inactive?
* What languages dominate my work?
* Which projects improved over time?

---

### 7.2 Use SQL for analysis

Examples:

* ranking queries
* grouping by language
* activity trends

---

## 8. Dashboard Layer

### 8.1 Keep it simple

Do NOT build a complex frontend.

Use:

* lightweight dashboard approach

---

### 8.2 Display

* Top repositories (ranked)
* Score breakdown
* Language distribution
* Activity summary

---

### 8.3 Data source

Dashboard MUST read from:

> PostgreSQL (not from API directly)

---

## 9. Testing (Minimal but important)

Test:

* DB connection works
* API returns expected shape
* pipeline runs without crashing

---

## 10. README (Your Most Important Deliverable)

Structure:

---

### Title

GitHub Data Pipeline & Portfolio Analyzer

---

### Problem

Selecting meaningful GitHub projects is subjective and inconsistent.

---

### Solution

Built a data pipeline that ingests GitHub data and ranks repositories using defined metrics.

---

### Architecture

Explain flow:

```
GitHub API → Ingestion → PostgreSQL → Transformation → Dashboard
```

---

### Tech Stack

* Python
* PostgreSQL
* Scheduling (cron or similar)
* Dashboard tool

---

### Features

* automated data ingestion
* scoring algorithm
* persistent storage
* analytics dashboard

---

### Screenshots

* DB tables
* dashboard
* output rankings

---

## 11. Final Checklist (Before You Call It “Portfolio-Ready”)

* [ ] Data stored in PostgreSQL
* [ ] Pipeline runs end-to-end without manual fixes
* [ ] Scores are computed and stored
* [ ] Dashboard reads from DB
* [ ] README explains system clearly
* [ ] You can explain architecture without hesitation

---

## 12. Common Failure Points (Avoid These)

* building everything in one script
* skipping database design
* no transformation logic
* focusing too much on UI
* unclear README

---

## 13. Upgrade Path (After MVP)

Only after finishing:

* incremental updates instead of overwrite
* multiple GitHub users
* scheduling automation
* deployment (optional)

---

## Final Note

If you follow this plan strictly, you will end up with:

> A legitimate **data engineering portfolio project**, not a beginner script.

If you skip structure, you’ll end up with something that looks like coursework.

Stick to the pipeline.

---

## 14. Version 2.0 Shift: The Curation Layer (Hybrid Open-Source Tool)

Once the MVP is complete, the project evolves from a personal script into a **General-Purpose Portfolio Tool**.

The goal is to combine **immutable data signals** (automated pipeline) with **human judgment** (curation) without destroying data credibility.

### 14.1 Architecture: Separation of Concerns
Never allow users to manually edit pipeline-generated scores or raw commits. Instead, introduce a strict separation:
*   **System Data (Immutable):** Managed by `src/ingest.py`. (Commits, raw scores, recency).
*   **User Data (Editable):** Managed by the UI. Stored in a new table `repo_overrides`.

### 14.2 The `repo_overrides` Table
*   `repo_id` (Primary Key)
*   `project_type` (system, practice, standard)
*   `display_name` (optional clean name)
*   `is_featured` (boolean)

SQL views (e.g., `analytics_views.sql`) will merge the immutable system data with the `repo_overrides` table to produce the final dashboard view.

### 14.3 Two-Mode Dashboard (Streamlit)
The dashboard must evolve to support two modes:
1.  **View Mode (Recruiter):** The clean, progressively disclosed portfolio ranking.
2.  **Edit Mode (Curation):** An interactive UI (`st.data_editor`) where developers can classify their projects (`system` vs `practice`) and input external contributions.

*This pivot turns the project from a simple dashboard into a complete Decision-Support Product.*
