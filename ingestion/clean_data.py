import os
import traceback

import pandas as pd
from dotenv import load_dotenv
from psycopg2 import sql

from database.db_connection import connect_postgres

load_dotenv()


def clean_and_transform(recreate=False):
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
            cursor.execute("DROP TABLE IF EXISTS train_delays_cleaned;")

        query = "SELECT * FROM train_delays_raw;"
        df = pd.read_sql(query, conn)

        df.rename(columns={
            "distance(Km)": "distance_km",
            "sc_arr__time": "sc_arr_time",
            "dealy_min": "delay_min",
        }, inplace=True)

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['sc_arr_time'] = pd.to_datetime(df['sc_arr_time'], format="%H:%M:%S").dt.time
        df['act_arr_time'] = pd.to_datetime(df['act_arr_time'], format="%H:%M:%S").dt.time
        df['delay_min'] = pd.to_datetime(df['delay_min'], format="%H:%M:%S").dt.time

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_cleaned (
            train_id VARCHAR(50),
            train_name VARCHAR(100),
            train_no INT,
            source VARCHAR(100),
            destination VARCHAR(100),
            date TIMESTAMP,
            "distance_km" INT,
            sc_arr_time TIME,
            act_arr_time TIME,
            delay_min TIME,
            season VARCHAR(50),
            run_frequency VARCHAR(50)
        );
        """)
        conn.commit()
        print("📌 Table created successfully")

        for _, row in df.iterrows():
            cursor.execute(
                sql.SQL("""
                    INSERT INTO train_delays_cleaned (
                        train_id, train_name, train_no, source, destination, date,
                        "distance_km", sc_arr_time, act_arr_time, delay_min,
                        season, run_frequency
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """),
                (
                    row['train_id'], row['train_name'], row['train_no'],
                    row['source'], row['destination'], row['date'],
                    row['distance_km'], row['sc_arr_time'], row['act_arr_time'],
                    row['delay_min'], row['season'], row['run_frequency']
                )
            )

        conn.commit()
        print("🚂 Cleaned data loaded into train_delays_cleaned successfully!")

        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    clean_and_transform()
