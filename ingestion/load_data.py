import pandas as pd
from psycopg2 import sql
from database.db_connection import connect_postgres   # ✅ import your existing function
from dotenv import load_dotenv

import os
load_dotenv()

def load_csv_to_postgres(csv_path):
    host=os.getenv("host")
    dbname=os.getenv("dbname")
    user=os.getenv("user")
    password=os.getenv("password")
    port=5432
    try:
        # Use your existing connection function
        conn = connect_postgres(host,dbname,user,password,port)
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL")

        # Create table (adjust schema to match your CSV)
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

        # Load CSV data
        df = pd.read_csv(csv_path)
        #df['Date'] = pd.to_datetime(df['Date'], format="%d-%m-%Y %H:%M")
        #print(df.dtypes)
        # Insert rows into table
        for _, row in df.iterrows():
            cursor.execute(
                sql.SQL("""INSERT INTO train_delays_raw (train_id, train_name, train_no, source, destination, date, "distance(Km)", sc_arr__time, act_arr_time, dealy_min, season, run_frequency) VALUES (%s, %s, %s, %s, %s ,%s, %s, %s, %s, %s, %s, %s)"""),
                (row['Train_id'], row['Train_name'], row['Train_no'], row['Source'], row['Destitnation'], row['Date'], row['Distance(Km)'], row['Sc_arr__time'], row['Act_arr_time'], row['Dealy_min'], row['Season'], row['Run_frequency'])
            )
        conn.commit()
        print("🚂 Data loaded successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    load_csv_to_postgres("data/raw/indian_railway_delay_data_.csv")
