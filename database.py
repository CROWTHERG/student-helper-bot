# database.py
import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS past_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        course TEXT,
        level TEXT,
        year TEXT,
        uploaded_by TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, user):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO past_questions (file_path, course, level, year, uploaded_by) VALUES (?, ?, ?, ?, ?)",
                (file_path, course, level, year, user))
    conn.commit()
    conn.close()

def get_past_questions(course, level, year):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM past_questions WHERE course=? AND level=? AND year=?", (course, level, year))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]