import psycopg2

def test_connection():
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="guardian",
        user="guardian",
        password="guardian"
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    conn.close()
