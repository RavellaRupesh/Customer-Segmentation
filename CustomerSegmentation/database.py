"""Optional MySQL connection helper.

Set DB_PASSWORD in your terminal before using this module.
Example PowerShell: $env:DB_PASSWORD = "your-local-password"
"""
import os
import mysql.connector

def get_connection():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not set. Set it in your terminal before connecting."
        )
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=password,
        database=os.getenv("DB_NAME", "customer_segmentation"),
    )
