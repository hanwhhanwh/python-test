from flask import current_app
from sqlalchemy import create_engine

DDB_HOST = "127.0.0.1"
DDB_PORT = "3306"
DDB_USER_ID = "dispenser"
DDB_PASSWORD = "dispenser@21"
DDB_DATABASE = "DISPENSER"

DB_URL = f"mysql+mysqlconnector://{DDB_USER_ID}:{DDB_PASSWORD}@{DDB_HOST}:{DDB_PORT}/{DDB_DATABASE}?charset=utf8"

def connect_database():
    database = create_engine(DB_URL, encoding = 'utf-8')
    return database

