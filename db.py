import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


db_user = os.getenv('POSTGRESQLCONNSTR_DB_USER') or os.getenv('DB_USER')
db_pw = os.getenv('POSTGRESQLCONNSTR_DB_PASSWORD') or os.getenv('DB_PASSWORD')
db_host = os.getenv('POSTGRESQLCONNSTR_DB_HOST') or os.getenv('DB_HOST')
db_port = os.getenv('POSTGRESQLCONNSTR_DB_PORT') or os.getenv('DB_PORT')
db_name = os.getenv('POSTGRESQLCONNSTR_DB_NAME') or os.getenv('DB_NAME')

# db_user = os.getenv('DB_USER')
# db_pw = os.getenv('DB_PASSWORD')
# db_host = os.getenv('DB_HOST')
# db_port = os.getenv('DB_PORT')
# db_name = os.getenv('DB_NAME')

conn_str = f'postgresql://{db_user}:{db_pw}@{db_host}:{db_port}/{db_name}'
print(conn_str)

def get_db_conn():
    print("conn_str", conn_str)
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    return conn

# get_db_conn()