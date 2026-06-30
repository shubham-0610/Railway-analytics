import os
import traceback

from dotenv import load_dotenv

from database.db_connection import connect_postgres

load_dotenv()


def transform_for_dashboard(recreate=False):
    try:
        conn = connect_postgres()
        print("✅ Connected to DuckDB")

        if recreate:
            conn.execute("DROP TABLE IF EXISTS train_delays_dashboard")

        conn.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_dashboard (
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
            run_frequency VARCHAR,
            day INTEGER,
            month INTEGER,
            hour INTEGER,
            minute INTEGER,
            delay_category VARCHAR
        )
        """)
        print("📌 Dashboard table created successfully")

        conn.execute("""
        INSERT INTO train_delays_dashboard (
            train_id, train_name, train_no, source, destination, date,
            distance_km, sc_arr_time, act_arr_time, delay_min,
            season, run_frequency, day, month, hour, minute, delay_category
        )
        SELECT
            train_id,
            train_name,
            train_no,
            source,
            destination,
            date,
            distance_km,
            sc_arr_time,
            act_arr_time,
            delay_min,
            season,
            run_frequency,
            EXTRACT(DAY FROM date) AS day,
            EXTRACT(MONTH FROM date) AS month,
            EXTRACT(HOUR FROM sc_arr_time) AS hour,
            EXTRACT(MINUTE FROM sc_arr_time) AS minute,
            CASE
                WHEN EXTRACT(HOUR FROM delay_min)*60 + EXTRACT(MINUTE FROM delay_min) <= 5 THEN 'On Time'
                WHEN EXTRACT(HOUR FROM delay_min)*60 + EXTRACT(MINUTE FROM delay_min) <= 30 THEN 'Minor Delay'
                WHEN EXTRACT(HOUR FROM delay_min)*60 + EXTRACT(MINUTE FROM delay_min) <= 120 THEN 'Moderate Delay'
                ELSE 'Severe Delay'
            END AS delay_category
        FROM train_delays_cleaned
        """)
        print("🚂 Dashboard data loaded successfully!")
        conn.close()

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    transform_for_dashboard()
