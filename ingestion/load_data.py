import os

import pandas as pd
from dotenv import load_dotenv
from psycopg2 import sql

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


def load_csv_to_postgres(csv_path, recreate=False):
    host = os.getenv("host")
    dbname = os.getenv("dbname")
    user = os.getenv("user")
    password = os.getenv("password")
    port = 5432
    try:
        conn = connect_postgres(host, dbname, user, password, port)
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")

        if recreate:
            cursor.execute("DROP TABLE IF EXISTS train_delays_raw;")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_raw (
            train_id VARCHAR(50),
            train_name VARCHAR(100),
            train_no INT,
            source VARCHAR(100),
            destination VARCHAR(100),
            date TIMESTAMP,
            "distance(Km)" INT,
            sc_arr__time TIME,
            act_arr_time TIME,
            dealy_min TIME,
            season VARCHAR(50),
            run_frequency VARCHAR(50)
        );
        """)
        conn.commit()
        print("📌 Table created successfully")

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            normalized_date = _normalize_date_value(row['Date'])
            cursor.execute(
                sql.SQL("""INSERT INTO train_delays_raw (train_id, train_name, train_no, source, destination, date, "distance(Km)", sc_arr__time, act_arr_time, dealy_min, season, run_frequency) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""),
                (row['Train_id'], row['Train_name'], row['Train_no'], row['Source'], row['Destitnation'], normalized_date, row['Distance(Km)'], row['Sc_arr__time'], row['Act_arr_time'], row['Dealy_min'], row['Season'], row['Run_frequency'])
            )
        conn.commit()
        print("🚂 Data loaded successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print("❌ Error:", e)


if __name__ == "__main__":
    load_csv_to_postgres("data/raw/indian_railway_delay_data_.csv")
