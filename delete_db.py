import mysql.connector
from dotenv import load_dotenv

import os

load_dotenv()

db_conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
db_cur = db_conn.cursor()

db_cur.execute("SHOW TABLES")
tables = db_cur.fetchall()

for (table_name,) in tables:
    print(f"Dropping table: {table_name}")
    db_cur.execute(f"DROP TABLE IF EXISTS `{table_name}`")

db_conn.commit()

db_cur.close()
db_conn.close()
