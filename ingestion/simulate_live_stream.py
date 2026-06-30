from datetime import date, datetime, timedelta
import os

import pandas as pd

from database.db_connection import connect_postgres


def build_simulated_delay_payload(train_name, delay_minutes=15, latest_date=None):
    """Create a single synthetic delay record for the next day."""
    base_date = latest_date or date.today()
    next_date = base_date + timedelta(days=1)
    scheduled_time = "06:30:00"
    actual_time = (
        datetime.strptime(scheduled_time, "%H:%M:%S") + timedelta(minutes=delay_minutes)
    ).strftime("%H:%M:%S")

    return {
        "train_name": train_name,
        "date": next_date,
        "sc_arr_time": scheduled_time,
        "act_arr_time": actual_time,
    }


def ensure_dashboard_table(conn):
    """Create the dashboard table if it does not already exist."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS train_delays_dashboard (
            train_name VARCHAR(100),
            date DATE,
            sc_arr_time TIME,
            act_arr_time TIME
        );
        """
    )
    conn.commit()
    cursor.close()


def get_latest_train_date(conn, train_name):
    """Return the latest date for the selected train if one exists."""
    query = "SELECT MAX(date) AS latest_date FROM train_delays_dashboard WHERE train_name = %s;"
    latest_df = pd.read_sql(query, conn, params=(train_name,))
    latest_value = latest_df.iloc[0][0]

    if pd.isna(latest_value):
        return None

    return pd.Timestamp(latest_value).date()


def insert_simulated_delay(train_name, delay_minutes=15, conn=None):
    """Insert one synthetic delay entry into the dashboard table."""
    if conn is None:
        host = os.getenv("host")
        dbname = os.getenv("dbname")
        user = os.getenv("user")
        password = os.getenv("password")
        port = 5432
        conn = connect_postgres(host, dbname, user, password, port)

    if conn is None:
        raise ConnectionError("Unable to connect to PostgreSQL.")

    ensure_dashboard_table(conn)

    latest_date = get_latest_train_date(conn, train_name)
    payload = build_simulated_delay_payload(
        train_name=train_name,
        delay_minutes=delay_minutes,
        latest_date=latest_date,
    )

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO train_delays_dashboard (train_name, date, sc_arr_time, act_arr_time)
        VALUES (%s, %s, %s, %s)
        """,
        (
            payload["train_name"],
            payload["date"],
            payload["sc_arr_time"],
            payload["act_arr_time"],
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return payload
