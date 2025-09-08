# database.py
import sqlite3
import os

DB_PATH = "storage/bot.db"

def init_db():
    os.makedirs("storage", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS past_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            course TEXT,
            level TEXT,
            year TEXT,
            uploaded_by TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, uploaded_by):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO past_questions (file_path, course, level, year, uploaded_by)
        VALUES (?, ?, ?, ?, ?)
    """, (file_path, course, level, year, uploaded_by))
    conn.commit()
    conn.close()

def get_past_questions(course, level, year):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT file_path FROM past_questions
        WHERE course=? AND level=? AND year=?
    """, (course, level, year))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
