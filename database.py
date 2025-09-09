import sqlite3
import os

DB_PATH = "storage/past_questions.db"

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
            semester TEXT,
            uploader TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, semester, uploader):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO past_questions (file_path, course, level, year, semester, uploader) VALUES (?, ?, ?, ?, ?, ?)",
        (file_path, course.upper(), level.upper(), year, semester, uploader)
    )
    conn.commit()
    conn.close()

def get_grouped_past_questions(level, year, semester):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT course, file_path FROM past_questions
        WHERE level = ? AND year = ? AND semester = ?
        ORDER BY course
    """, (level.upper(), year, semester))
    rows = c.fetchall()
    conn.close()

    grouped = {}
    for course, file_path in rows:
        if course not in grouped:
            grouped[course] = []
        grouped[course].append(file_path)
    return grouped
