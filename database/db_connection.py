import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

import os
load_dotenv()

def connect_postgres(host="localhost", dbname="demo", user="demo", password="demo", port=5432):
    """
    Connects to a local PostgreSQL database and tests the connection.
    
    Parameters:
        host (str): Database host (default: localhost)
        dbname (str): Database name
        user (str): Username
        password (str): Password
        port (int): Port number (default: 5432)
    
    Returns:
        connection object if successful, None otherwise
    """
    try:
        conn = psycopg2.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            port=port
        )
        print("✅ Connection to PostgreSQL successful!")
        return conn
    except OperationalError as e:
        print("❌ Connection failed!")
        print(e)
        return None


#Example usage:
# if __name__ == "__main__":
#     connection = connect_postgres(
#         host=os.getenv("host"),
#         dbname=os.getenv("dbname"),   # replace with your DB name
#         user=os.getenv("user"),       # replace with your pgAdmin username
#         password=os.getenv("password"),  # replace with your pgAdmin password
#         port=5432
#     )
    
#     if connection:
#         # Test query
#         cursor = connection.cursor()
#         cursor.execute("SELECT version();")
#         record = cursor.fetchone()
#         print("PostgreSQL version:", record)
#         cursor.close()
#         connection.close()
