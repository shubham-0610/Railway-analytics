import calendar
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db_connection import connect_postgres
from ingestion.pipeline import initialize_dashboard_data, refresh_dashboard_with_sample

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))


def load_dashboard_data():
    host = os.getenv("host")
    dbname = os.getenv("dbname")
    user = os.getenv("user")
    password = os.getenv("password")
    port = 5432

    conn = connect_postgres(host, dbname, user, password, port)
    if conn is None:
        st.error("Unable to connect to PostgreSQL. Please verify your database settings.")
        st.stop()

    query = "SELECT train_name, date, sc_arr_time, act_arr_time FROM train_delays_dashboard;"
    df = pd.read_sql(query, conn)

    if df.empty:
        try:
            conn.close()
            initialize_dashboard_data()
            conn = connect_postgres(host, dbname, user, password, port)
            df = pd.read_sql(query, conn)
        except Exception as exc:
            st.warning(f"Data initialization failed: {exc}")

    conn.close()

    if df.empty:
        return pd.DataFrame(columns=["train_name", "date", "sc_arr_time", "act_arr_time"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    def time_to_minutes(value):
        if pd.isna(value):
            return None
        text_value = str(value)
        try:
            parsed = pd.to_datetime(text_value, format="%H:%M:%S", errors="coerce")
            if pd.isna(parsed):
                return None
            return parsed.hour * 60 + parsed.minute + parsed.second / 60
        except Exception:
            return None

    scheduled_minutes = df["sc_arr_time"].apply(time_to_minutes)
    actual_minutes = df["act_arr_time"].apply(time_to_minutes)
    df["delay_minutes"] = (pd.Series(actual_minutes) - pd.Series(scheduled_minutes))
    return df


def get_day_options(year_value=None, month_value=None):
    if month_value in [None, "All", ""]:
        return ["All"] + [str(day) for day in range(1, 32)]

    year = int(year_value) if year_value not in [None, "All", ""] else pd.Timestamp.today().year
    month = int(month_value)
    last_day = calendar.monthrange(year, month)[1]
    return ["All"] + [str(day) for day in range(1, last_day + 1)]


def build_trend_data(df, selected_train, granularity, year_value=None, month_value=None, day_value=None):
    train_df = df[df["train_name"] == selected_train].copy()

    if train_df.empty:
        return pd.DataFrame(columns=["time_unit", "delay_minutes"])

    train_df["date"] = pd.to_datetime(train_df["date"], errors="coerce")
    train_df = train_df.dropna(subset=["date"])

    if year_value not in [None, "All", ""]:
        train_df = train_df[train_df["date"].dt.year == int(year_value)]
    if month_value not in [None, "All", ""]:
        train_df = train_df[train_df["date"].dt.month == int(month_value)]
    if day_value not in [None, "All", ""]:
        train_df = train_df[train_df["date"].dt.day == int(day_value)]

    if train_df.empty:
        return pd.DataFrame(columns=["time_unit", "delay_minutes"])

    if granularity == "None":
        train_df["time_unit"] = train_df["date"].dt.strftime("%Y-%m-%d")
    elif granularity == "Day":
        train_df["time_unit"] = train_df["date"].dt.date
    elif granularity == "Month":
        train_df["time_unit"] = train_df["date"].dt.to_period("M").astype(str)
    else:
        train_df["time_unit"] = train_df["date"].dt.year

    return train_df.groupby("time_unit", as_index=False)["delay_minutes"].mean()


def main():
    st.title("🚆 Train Delay Trends Dashboard")

    df = load_dashboard_data()

    if df.empty:
        st.info("No data is available yet. Use the refresh button to simulate a new live entry.")
        return

    train_list = df["train_name"].dropna().unique().tolist()
    if not train_list:
        st.info("No train data is available yet. Try refreshing again after the pipeline finishes.")
        return

    selected_train = st.selectbox("Select Train:", train_list)

    current_year = pd.Timestamp.today().year
    year_options = ["All"] + [str(year) for year in range(current_year - 4, current_year + 1)]
    year_filter = st.selectbox("Year", year_options, index=0)

    month_filter = st.selectbox("Month", ["All"] + [str(month) for month in range(1, 13)], index=0)
    day_options = get_day_options(year_filter, month_filter)
    day_filter = st.selectbox("Day", day_options, index=0)

    granularity = st.selectbox("View trends by:", ["None", "Day", "Month", "Year"], index=1)

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Sync / Refresh"):
            try:
                payload = refresh_dashboard_with_sample(selected_train)
                df = load_dashboard_data()
                train_list = df["train_name"].dropna().unique().tolist()
                if train_list and selected_train not in train_list:
                    selected_train = train_list[0]
                st.session_state["refresh_message"] = (
                    f"Added a new live entry for {payload['train_name']} on {payload['date']} "
                    f"with {payload['delay_minutes']} min delay"
                )
                st.session_state["refresh_data"] = df
            except Exception as exc:
                st.session_state["refresh_message"] = f"Refresh failed: {exc}"

    if "refresh_message" in st.session_state:
        st.success(st.session_state["refresh_message"])

    if "refresh_data" in st.session_state and st.session_state["refresh_data"] is not None:
        df = st.session_state["refresh_data"]

    trend_df = build_trend_data(df, selected_train, granularity, year_filter, month_filter, day_filter)

    st.subheader(f"📈 {granularity}-wise Delay Trend for {selected_train}")
    if trend_df.empty:
        st.info("No records match the selected year, month, and day filters.")
    else:
        st.line_chart(trend_df.set_index("time_unit"))


if __name__ == "__main__":
    main()
