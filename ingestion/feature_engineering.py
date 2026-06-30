import os
import traceback

from dotenv import load_dotenv

from database.db_connection import connect_postgres

load_dotenv()


def transform_for_dashboard(recreate=False):
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
            cursor.execute("DROP TABLE IF EXISTS train_delays_dashboard;")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_delays_dashboard (
            train_id VARCHAR(50),
            train_name VARCHAR(100),
            train_no INT,
            source VARCHAR(100),
            destination VARCHAR(100),
            date TIMESTAMP,
            distance_km INT,
            sc_arr_time TIME,
            act_arr_time TIME,
            delay_min TIME,
            season VARCHAR(50),
            run_frequency VARCHAR(50),
            day INT,
            month INT,
            hour INT,
            minute INT,
            delay_category VARCHAR(50)
        );
        """)
        conn.commit()
        print("📌 Dashboard table created successfully")

        cursor.execute("""
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
        FROM train_delays_cleaned;
        """)
        conn.commit()
        print("🚂 Dashboard data loaded successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()


if __name__ == "__main__":
    transform_for_dashboard()
