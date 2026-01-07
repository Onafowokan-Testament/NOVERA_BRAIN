# ...existing code...
from pathlib import Path
import sqlite3
import pandas as pd
from loguru import logger

# Resolve CSV path relative to this script (timetable_agent/document/timetable_formatted.csv)
csv_path = Path(__file__).resolve().parents[2] / "document" / "timetable_formatted.csv"
db_path = Path(__file__).resolve().parents[2] / "timetable.db"

if not csv_path.exists():
    logger.error(f"Timetable data file not found: {csv_path}")
    raise FileNotFoundError(f"Missing file: {csv_path}")

try:
    df = pd.read_csv(csv_path)
    
except Exception:
    logger.exception(f"Error loading timetable data from {csv_path}")
    raise

logger.info("Loaded timetable, first rows:\n{}", df.head())

# Write to sqlite using context manager
try:
    with sqlite3.connect(db_path) as conn:
        df.to_sql("timetable", conn, if_exists="replace", index=False)
    logger.success(f"Timetable written to {db_path}")
except Exception:
    logger.exception(f"Failed writing timetable to {db_path}")
    raise
# ...existing code...