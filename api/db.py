import os
import psycopg2.pool
import atexit
import logging
from dotenv import load_dotenv

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

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
            logger.debug("Connection pool created successfully")
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to database: {e}")
            self.pool = None

    def get_connection(self):
        if self.pool:
            logger.debug("Getting connection from pool")
            return self.pool.getconn()
        else:
            logger.error("Connection pool is not initialized")
            raise Exception("Connection pool is not initialized")

    def return_connection(self, conn):
        if self.pool:
            logger.debug("Returning connection to pool")
            self.pool.putconn(conn)
        else:
            logger.error("Cannot return connection. Pool is not initialized")

    def close_all_connections(self):
        if self.pool:
            logger.debug("Closing all connections")
            self.pool.closeall()
        else:
            logger.error("Cannot close connections. Pool is not initialized")

def initializeConnectionPool():
    global pool
    pool = ConnectionPool()
    logger.debug(f"Initialized ConnectionPool: {pool}")

# Uncomment jika Anda ingin menutup koneksi saat keluar
# atexit.register(lambda: pool.close_all_connections() if pool else None)