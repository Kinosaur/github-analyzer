import os
import logging
import time
from dotenv import load_dotenv
from github_client import GitHubClient
from db import DatabaseConnector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "github_db")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    github_token = os.getenv("GITHUB_TOKEN")

    client = GitHubClient(token=github_token)
    db = DatabaseConnector(db_host, db_port, db_user, db_password, db_name)
    db.connect()

    try:
        # Fetch all repos from database
        with db.conn.cursor() as cur:
            cur.execute("SELECT id, full_name FROM repos;")
            repos = cur.fetchall()

        logger.info(f"Checking READMEs for {len(repos)} repositories...")

        updates = []
        for repo_id, full_name in repos:
            # Hit GitHub API for README
            resp = client.session.get(f"https://api.github.com/repos/{full_name}/readme")
            has_readme = (resp.status_code == 200)
            
            updates.append((has_readme, repo_id))
            
            # Simple sleep to not hammer the API too aggressively since it's just 40 requests
            time.sleep(0.1)

        # Update the database
        with db.conn.cursor() as cur:
            from psycopg2.extras import execute_values
            # execute_values is best for batch updates with a temp table or FROM VALUES
            query = """
                UPDATE repos AS r
                SET has_readme = v.has_readme
                FROM (VALUES %s) AS v(has_readme, id)
                WHERE r.id = v.id;
            """
            execute_values(cur, query, updates)
            db.conn.commit()
            
        logger.info(f"Successfully backfilled has_readme for {len(updates)} repositories.")

    except Exception as e:
        logger.error(f"Failed to backfill readmes: {e}")
        db.conn.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
