import os
import psycopg2.pool
import atexit
from dotenv import load_dotenv

pool = None 


class ConnectionPool:
    def __init__(self):
        self.min_conn = 1
        self.max_conn = 5
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                self.min_conn, 
                self.max_conn,
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
        except psycopg2.OperationalError as e:
            print(f"Failed to connect to database: {e}")

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def close_all_connections(self):
        self.pool.closeall()

def initializeConnectionPool():
    global pool
    pool = ConnectionPool()
    print(pool)


# atexit.register(lambda: pool.close_all_connections() if pool else None)

# __all__ = ['pool', 'ConnectionPool', 'initializeConnectionPool']