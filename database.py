import sqlite3

DATABASE_NAME = "tea.db"

def create_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    return connection