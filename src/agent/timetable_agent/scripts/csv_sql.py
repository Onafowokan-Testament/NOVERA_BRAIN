import pandas as pd
from sqlalchemy import create_engine

csv_file_path = "timetable_doc.csv"

data = pd.read_csv(csv_file_path)

print(data.head(5))

engine = create_engine("sqlite:///data.db")

data.to_sql("timetable", engine, index=False, if_exists="replace")
