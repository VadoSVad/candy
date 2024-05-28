# db.py
import mysql.connector
from contextlib import contextmanager

def connect_to_database(role):
    if role == "administrator":
        return mysql.connector.connect(
            host="localhost",
            user="admin",
            password="admin",
            database="candy_factory"
        )
    elif role == "buhgalter":
        return mysql.connector.connect(
            host="localhost",
            user="buhgalter",
            password="buhgalter",
            database="candy_factory"
        )
    elif role == "driver":
        return mysql.connector.connect(
            host="localhost",
            user="driver",
            password="driver",
            database="candy_factory"
        )

@contextmanager
def database_connection(role):
    conn = connect_to_database(role)
    try:
        yield conn
    finally:
        conn.close()