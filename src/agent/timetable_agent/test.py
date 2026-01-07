import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parents[2] / "timetable.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())  # Should show [('timetable',)]
