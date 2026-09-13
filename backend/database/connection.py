import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "altaria.proxy.rlwy.net",
    "port": 14337,
    "user": "root",
    "password": "wxyxMnJVOfMtujolDwgDcfJeWUFvlkoK",
    "database": "railway",
    "autocommit": False,
    "connection_timeout": 10,
}

def get_db_connection():
    required = ("host", "user", "password", "database")
    missing = [key for key in required if not DB_CONFIG.get(key)]
    if missing:
        print(f"Faltan variables de MySQL: {', '.join(missing)}")
        return None
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as exc:
        print(f"Error conectando a MySQL: {exc}")
        return None
