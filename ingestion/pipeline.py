import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from ingestion.clean_data import clean_and_transform
from ingestion.feature_engineering import transform_for_dashboard
from ingestion.load_data import load_csv_to_postgres

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


def initialize_dashboard_data(csv_path=None):
    """Load the CSV into PostgreSQL and build the dashboard tables."""
    csv_path = Path(csv_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "indian_railway_delay_data_.csv"))

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    load_csv_to_postgres(str(csv_path), recreate=True)
    clean_and_transform(recreate=True)
    transform_for_dashboard(recreate=True)


def refresh_dashboard_with_sample(train_name, csv_path=None, delay_minutes=15):
    """Append a new sample row to the raw CSV and rebuild the dashboard pipeline."""
    csv_path = Path(csv_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "indian_railway_delay_data_.csv"))

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError("The source CSV is empty.")

    if train_name not in df["Train_name"].astype(str).tolist():
        train_name = df.iloc[0]["Train_name"]

    train_rows = df[df["Train_name"].astype(str) == str(train_name)].copy()
    if train_rows.empty:
        raise ValueError(f"No rows found for train: {train_name}")

    latest_row = train_rows.iloc[-1]
    latest_date = pd.to_datetime(latest_row["Date"], format="%d-%m-%Y %H:%M")
    next_date = latest_date + timedelta(days=1)

    scheduled_time = str(latest_row["Sc_arr__time"])
    scheduled_dt = datetime.strptime(scheduled_time, "%H:%M:%S")
    random_delay = random.randint(5, 45)
    actual_dt = scheduled_dt + timedelta(minutes=random_delay)

    new_row = {
        "Train_id": f"SIM-{int(datetime.now().timestamp())}",
        "Train_name": train_name,
        "Train_no": int(latest_row["Train_no"]),
        "Source": latest_row["Source"],
        "Destitnation": latest_row["Destitnation"],
        "Date": next_date.strftime("%d-%m-%Y %H:%M"),
        "Distance(Km)": int(latest_row["Distance(Km)"]),
        "Sc_arr__time": scheduled_time,
        "Act_arr_time": actual_dt.strftime("%H:%M:%S"),
        "Dealy_min": actual_dt.strftime("%H:%M:%S"),
        "Season": latest_row["Season"],
        "Run_frequency": latest_row["Run_frequency"],
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(csv_path, index=False)

    initialize_dashboard_data(str(csv_path))

    return {
        "train_name": train_name,
        "date": new_row["Date"],
        "delay_minutes": random_delay,
        "csv_path": str(csv_path),
    }
