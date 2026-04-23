import os
import logging
from dotenv import load_dotenv
from github_client import GitHubClient
from db import DatabaseConnector
from datetime import datetime, timezone
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_iso_date(date_str):
    if not date_str:
        return None
    return datetime.strptime(date_str.replace('Z', '+0000'), "%Y-%m-%dT%H:%M:%S%z")

def main():
    load_dotenv()

    # DB Config
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "github_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN is missing. Please set it in .env")
        return

    client = GitHubClient(token=github_token)
    db = DatabaseConnector(db_host, db_port, db_user, db_password, db_name)
    
    try:
        db.connect()
        logger.info("Connected to database.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    repos_processed = 0
    commits_processed = 0
    status = "SUCCESS"
    error_msg = None

    try:
        logger.info("Fetching authenticated user's repositories...")
        # Get repos for the authenticated user
        raw_repos = client.fetch_all_pages("/user/repos", params={"visibility": "all", "affiliation": "owner"})
        
        repos_data = []
        for r in raw_repos:
            repos_data.append((
                r['id'],
                r.get('name'),
                r.get('full_name'),
                r.get('description'),
                r.get('html_url'),
                r.get('private', False),
                r.get('fork', False),
                parse_iso_date(r.get('created_at')),
                parse_iso_date(r.get('updated_at')),
                parse_iso_date(r.get('pushed_at')),
                r.get('size', 0),
                r.get('stargazers_count', 0),
                r.get('forks_count', 0),
                r.get('open_issues_count', 0),
                r.get('language'),
                r.get('topics', [])
            ))

        if repos_data:
            db.upsert_repos(repos_data)
            repos_processed = len(repos_data)
            logger.info(f"Upserted {repos_processed} repositories.")

        # Process each repo for languages and commits
        for repo in raw_repos:
            repo_id = repo['id']
            full_name = repo['full_name']
            
            logger.info(f"Processing details for repo: {full_name}")

            # 1. Fetch Languages
            lang_data = client.get(f"/repos/{full_name}/languages").json()
            if lang_data:
                languages_to_insert = [
                    (repo_id, lang, bytes_count) 
                    for lang, bytes_count in lang_data.items()
                ]
                db.upsert_repo_languages(languages_to_insert)

            # 2. Fetch Commits (max 100 recent commits to save API calls, as agreed)
            # Not using fetch_all_pages here to respect limits. 
            commits_resp = client.get(f"/repos/{full_name}/commits", params={"per_page": 100})
            if commits_resp.status_code == 200:
                raw_commits = commits_resp.json()
                if isinstance(raw_commits, list):
                    commits_data = []
                    for c in raw_commits:
                        commit_info = c.get('commit', {})
                        author_info = commit_info.get('author', {})
                        
                        commits_data.append((
                            c.get('sha'),
                            repo_id,
                            author_info.get('name'),
                            author_info.get('email'),
                            parse_iso_date(author_info.get('date')),
                            commit_info.get('message')
                        ))
                    
                    if commits_data:
                        db.upsert_commits(commits_data)
                        commits_processed += len(commits_data)
            elif commits_resp.status_code == 409:
                # 409 Conflict typically means repository is empty
                logger.info(f"Repo {full_name} is empty, skipping commits.")
            else:
                logger.warning(f"Failed to fetch commits for {full_name}: {commits_resp.status_code}")

    except Exception as e:
        status = "FAILED"
        error_msg = str(e)
        logger.error(f"Pipeline failed: {e}", exc_info=True)

    finally:
        # Log the run
        run_id = db.log_run(status, repos_processed, commits_processed, error_msg)
        logger.info(f"Pipeline run {run_id} finished with status {status}. Repos: {repos_processed}, Commits: {commits_processed}")
        db.close()

if __name__ == "__main__":
    main()
