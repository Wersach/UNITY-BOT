import logging
import psycopg2
import psycopg2.extras
from config import DATABASE_URL

logger = logging.getLogger(__name__)


def _conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS seen_repos (
                    id SERIAL PRIMARY KEY,
                    repo_url TEXT UNIQUE NOT NULL,
                    repo_name TEXT,
                    source_name TEXT DEFAULT 'GitHub',
                    generated_text TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pending_messages (
                    repo_id INTEGER PRIMARY KEY,
                    message_id INTEGER
                )
            """)
        conn.commit()
    logger.info("БД инициализирована")


def is_seen(repo_url: str) -> bool:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM seen_repos WHERE repo_url = %s", (repo_url,))
            return cur.fetchone() is not None


def add_repo(repo_url: str, repo_name: str, generated_text: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO seen_repos (repo_url, repo_name, generated_text, status)
                   VALUES (%s, %s, %s, 'pending') RETURNING id""",
                (repo_url, repo_name, generated_text),
            )
            repo_id = cur.fetchone()[0]
        conn.commit()
    return repo_id


def get_repo(repo_id: int) -> dict | None:
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM seen_repos WHERE id = %s", (repo_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def update_status(repo_id: int, status: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seen_repos SET status = %s WHERE id = %s", (status, repo_id))
        conn.commit()


def update_generated_text(repo_id: int, text: str):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seen_repos SET generated_text = %s WHERE id = %s", (text, repo_id))
        conn.commit()


def save_pending_message(repo_id: int, message_id: int):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO pending_messages (repo_id, message_id)
                   VALUES (%s, %s) ON CONFLICT (repo_id) DO UPDATE SET message_id = %s""",
                (repo_id, message_id, message_id),
            )
        conn.commit()


def get_stats() -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM seen_repos")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM seen_repos WHERE status='published'")
            published = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM seen_repos WHERE status='pending'")
            pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM seen_repos WHERE status='rejected'")
            rejected = cur.fetchone()[0]
    return {"total": total, "published": published, "pending": pending, "rejected": rejected}
