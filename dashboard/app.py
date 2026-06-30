import streamlit as st
import pandas as pd
from database.db_connection import connect_postgres
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    host = os.getenv("host")
    dbname = os.getenv("dbname")
    user = os.getenv("user")
    password = os.getenv("password")
    port = 5432

    st.title("🚆 Train Delay Trends Dashboard")

    # Connect to PostgreSQL
    conn = connect_postgres(host, dbname, user, password, port)

    # Query data
    query = "SELECT train_name, date, sc_arr_time, act_arr_time FROM train_delays_dashboard;"
    df = pd.read_sql(query, conn)
    conn.close()

    # Convert to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Calculate delay in minutes
    df["delay_minutes"] = (
        pd.to_timedelta(df["act_arr_time"].astype(str)) -
        pd.to_timedelta(df["sc_arr_time"].astype(str))
    ).dt.total_seconds() / 60

    # Dropdown to select train
    train_list = df["train_name"].unique().tolist()
    selected_train = st.selectbox("Select Train:", train_list)

    # Filter data for selected train
    train_df = df[df["train_name"] == selected_train].copy()

    # Choose granularity
    granularity = st.radio("View trends by:", ["Day", "Month", "Year"])

    if granularity == "Day":
        train_df["time_unit"] = train_df["date"].dt.date
    elif granularity == "Month":
        train_df["time_unit"] = train_df["date"].dt.to_period("M").astype(str)
    else:  # Year
        train_df["time_unit"] = train_df["date"].dt.year

    # Group by chosen time unit
    trend_df = train_df.groupby("time_unit")["delay_minutes"].mean().reset_index()

    # Line chart
    st.subheader(f"📈 {granularity}-wise Delay Trend for {selected_train}")
    st.line_chart(trend_df.set_index("time_unit"))

if __name__ == "__main__":
    main()
