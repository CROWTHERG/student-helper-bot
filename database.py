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
            file_path TEXT NOT NULL,
            course TEXT NOT NULL,
            level TEXT NOT NULL,
            year TEXT NOT NULL,
            semester TEXT NOT NULL,
            uploader TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, semester, uploader):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO past_questions (file_path, course, level, year, semester, uploader)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_path, course, level, year, semester, uploader))
    conn.commit()
    conn.close()

def get_past_questions(course=None, level=None, year=None, semester=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = "SELECT file_path FROM past_questions WHERE 1=1"
    params = []

    if course:
        query += " AND course = ?"
        params.append(course)
    if level:
        query += " AND level = ?"
        params.append(level)
    if year:
        query += " AND year = ?"
        params.append(year)
    if semester:
        query += " AND semester = ?"
        params.append(semester)

    c.execute(query, tuple(params))
    results = c.fetchall()
    conn.close()
    return [row[0] for row in results]
