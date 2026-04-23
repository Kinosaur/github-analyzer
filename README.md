# GitHub Data Pipeline & Portfolio Analyzer

## Problem
Selecting meaningful GitHub projects is subjective and inconsistent.

## Solution
Built a data pipeline that ingests GitHub data and ranks repositories using defined metrics.

## Architecture
```
GitHub API → Ingestion → PostgreSQL → Transformation → Dashboard
```

## Tech Stack
* Python
* PostgreSQL
* Scheduling (cron or similar)
* Dashboard tool

## Features
* automated data ingestion
* scoring algorithm
* persistent storage
* analytics dashboard
