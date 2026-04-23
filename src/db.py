import psycopg2
from psycopg2.extras import execute_values
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector:
    def __init__(self, host, port, user, password, dbname):
        self.conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname
        }
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(**self.conn_params)
        return self.conn

    def close(self):
        if self.conn is not None:
            self.conn.close()

    def upsert_repos(self, repos_data):
        query = """
            INSERT INTO repos (id, name, full_name, description, html_url, is_private, is_fork, created_at, updated_at, pushed_at, size_kb, stargazers_count, forks_count, open_issues_count, primary_language, topics)
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                full_name = EXCLUDED.full_name,
                description = EXCLUDED.description,
                html_url = EXCLUDED.html_url,
                is_private = EXCLUDED.is_private,
                is_fork = EXCLUDED.is_fork,
                updated_at = EXCLUDED.updated_at,
                pushed_at = EXCLUDED.pushed_at,
                size_kb = EXCLUDED.size_kb,
                stargazers_count = EXCLUDED.stargazers_count,
                forks_count = EXCLUDED.forks_count,
                open_issues_count = EXCLUDED.open_issues_count,
                primary_language = EXCLUDED.primary_language,
                topics = EXCLUDED.topics
        """
        with self.conn.cursor() as cur:
            execute_values(cur, query, repos_data)
        self.conn.commit()

    def upsert_repo_languages(self, languages_data):
        query = """
            INSERT INTO repo_languages (repo_id, language, byte_count)
            VALUES %s
            ON CONFLICT (repo_id, language) DO UPDATE SET
                byte_count = EXCLUDED.byte_count
        """
        with self.conn.cursor() as cur:
            execute_values(cur, query, languages_data)
        self.conn.commit()

    def upsert_commits(self, commits_data):
        query = """
            INSERT INTO commits (sha, repo_id, author_name, author_email, commit_date, message)
            VALUES %s
            ON CONFLICT (sha) DO NOTHING
        """
        # We do NOTHING on conflict because commits are immutable
        with self.conn.cursor() as cur:
            execute_values(cur, query, commits_data)
        self.conn.commit()

    def log_run(self, status, repos_processed, commits_processed, error_message=None):
        query = """
            INSERT INTO pipeline_runs (status, repos_processed, commits_processed, error_message)
            VALUES (%s, %s, %s, %s)
            RETURNING run_id
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (status, repos_processed, commits_processed, error_message))
            run_id = cur.fetchone()[0]
        self.conn.commit()
        return run_id
