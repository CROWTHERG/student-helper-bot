# database.py
import sqlite3
import os

DB_PATH = "bot.db"

def init_db():
    """Initialize the database and create table if not exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS past_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            course TEXT NOT NULL,
            level TEXT NOT NULL,
            year TEXT NOT NULL,
            semester TEXT NOT NULL,
            uploaded_by TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_past_question(file_path, course, level, year, semester, uploaded_by):
    """Save a past question record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO past_questions (file_path, course, level, year, semester, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_path, course, level, year, semester, uploaded_by))
    conn.commit()
    conn.close()

def get_past_questions_grouped(year, level, semester):
    """
    Get all past questions grouped by course for a given year, level, and semester.
    Returns a dictionary { course: [file_paths] }
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT course, file_path FROM past_questions
        WHERE year=? AND level=? AND semester=?
        ORDER BY course
    """, (year, level, semester))
    rows = cursor.fetchall()
    conn.close()

    grouped = {}
    for course, file_path in rows:
        grouped.setdefault(course, []).append(file_path)
    return grouped
