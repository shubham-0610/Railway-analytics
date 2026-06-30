import os
import traceback

import pandas as pd
from dotenv import load_dotenv

from database.db_connection import connect_postgres

load_dotenv()


def clean_and_transform(recreate=False):
    try:
        conn = connect_postgres()
        print("✅ Connected to DuckDB")

        if recreate:
            conn.execute("DROP TABLE IF EXISTS train_delays_cleaned")

        df = conn.execute("SELECT * FROM train_delays_raw").df()

        df.rename(columns={
            "distance(Km)": "distance_km",
            "sc_arr__time": "sc_arr_time",
            "dealy_min": "delay_min",
        }, inplace=True)

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['sc_arr_time'] = pd.to_datetime(df['sc_arr_time'], format="%H:%M:%S", errors='coerce').dt.time
        df['act_arr_time'] = pd.to_datetime(df['act_arr_time'], format="%H:%M:%S", errors='coerce').dt.time
        df['delay_min'] = pd.to_datetime(df['delay_min'], format="%H:%M:%S", errors='coerce').dt.time

        conn.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_cleaned (
            train_id VARCHAR,
            train_name VARCHAR,
            train_no INTEGER,
            source VARCHAR,
            destination VARCHAR,
            date TIMESTAMP,
            distance_km INTEGER,
            sc_arr_time TIME,
            act_arr_time TIME,
            delay_min TIME,
            season VARCHAR,
            run_frequency VARCHAR
        )
        """)
        print("📌 Table created successfully")

        conn.register("clean_df", df)
        conn.execute("INSERT INTO train_delays_cleaned SELECT * FROM clean_df")
        print("🚂 Cleaned data loaded into train_delays_cleaned successfully!")
        conn.close()
    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    clean_and_transform()
