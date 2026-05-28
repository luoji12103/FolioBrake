import os

import psycopg2


def test_connection():
    conn = psycopg2.connect(
        host=os.environ.get("TEST_DB_HOST", "localhost"),
        port=int(os.environ.get("TEST_DB_PORT", "5433")),
        database=os.environ.get("TEST_DB_NAME", "guardian"),
        user=os.environ.get("TEST_DB_USER", "guardian"),
        password=os.environ.get("TEST_DB_PASSWORD", "guardian"),
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    conn.close()
