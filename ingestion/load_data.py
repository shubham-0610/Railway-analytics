import os
import re

import pandas as pd
from dotenv import load_dotenv

from database.db_connection import connect_postgres

load_dotenv()


def _normalize_date_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        parsed = pd.to_datetime(value, format="%d-%m-%Y %H:%M", errors="coerce")
    else:
        parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _normalize_time_value(value):
    if pd.isna(value):
        return None
    raw_value = str(value).strip()
    if not raw_value:
        return None

    match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', raw_value)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3) or 0)
        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
            return f"{hour:02d}:{minute:02d}:{second:02d}"

    return None


def load_csv_to_postgres(csv_path, recreate=False):
    try:
        conn = connect_postgres()
        print("✅ Connected to DuckDB")

        if recreate:
            conn.execute("DROP TABLE IF EXISTS train_delays_raw")

        conn.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_raw (
            train_id VARCHAR,
            train_name VARCHAR,
            train_no INTEGER,
            source VARCHAR,
            destination VARCHAR,
            date TIMESTAMP,
            "distance(Km)" INTEGER,
            sc_arr__time TIME,
            act_arr_time TIME,
            dealy_min TIME,
            season VARCHAR,
            run_frequency VARCHAR
        )
        """)
        print("📌 Table created successfully")

        df = pd.read_csv(csv_path)
        df = df.copy()
        df["date"] = df["Date"].apply(_normalize_date_value)
        df["sc_arr__time"] = df["Sc_arr__time"].apply(_normalize_time_value)
        df["act_arr_time"] = df["Act_arr_time"].apply(_normalize_time_value)
        df["dealy_min"] = df["Dealy_min"].apply(_normalize_time_value)
        df = df[[
            "Train_id", "Train_name", "Train_no", "Source", "Destitnation", "date",
            "Distance(Km)", "sc_arr__time", "act_arr_time", "dealy_min", "Season", "Run_frequency"
        ]].rename(columns={
            "Train_id": "train_id",
            "Train_name": "train_name",
            "Train_no": "train_no",
            "Source": "source",
            "Destitnation": "destination",
            "date": "date",
            "Distance(Km)": "distance(Km)",
            "Sc_arr__time": "sc_arr__time",
            "Act_arr_time": "act_arr_time",
            "Dealy_min": "dealy_min",
            "Season": "season",
            "Run_frequency": "run_frequency",
        })

        conn.register("raw_df", df)
        conn.execute("INSERT INTO train_delays_raw SELECT * FROM raw_df")
        print("🚂 Data loaded successfully!")
        conn.close()

    except Exception as e:
        print("❌ Error:", e)


if __name__ == "__main__":
    load_csv_to_postgres("data/raw/indian_railway_delay_data_.csv")
