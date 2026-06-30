import os
import subprocess
import sys

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def _load_duckdb():
    try:
        import duckdb as duckdb_module
        return duckdb_module
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb"])
        import duckdb as duckdb_module
        return duckdb_module


def connect_postgres(host="localhost", dbname="demo", user="demo", password="demo", port=5432):
    """Create a DuckDB connection for local analytics workflows."""
    try:
        duckdb = _load_duckdb()
        db_path = os.getenv("duckdb_path", "data/railway.duckdb")
        conn = duckdb.connect(db_path)
        print("✅ Connection to DuckDB successful!")
        return conn
    except Exception as e:
        print("❌ Connection failed!")
        print(e)
        return None


def get_duckdb_connection():
    """Return a DuckDB connection using the configured local database path."""
    return connect_postgres()


def query_dataframe(conn, query, params=None):
    """Run a query and return a pandas DataFrame for either DuckDB or psycopg2-style connections."""
    if conn is None:
        raise ValueError("Connection is None")

    if hasattr(conn, "execute") and hasattr(conn, "fetchdf"):
        if params is None:
            return conn.execute(query).df()
        return conn.execute(query, params).df()

    if hasattr(conn, "cursor"):
        cursor = conn.cursor()
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        if cursor.description is None:
            cursor.close()
            return pd.DataFrame()
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows, columns=columns)

    return pd.read_sql(query, conn, params=params)
