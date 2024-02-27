import sqlite3
from configparser import ConfigParser

class DBAccess:
    def __init__(self, db_name=None):
        config = ConfigParser()
        config.read('config.ini')
        if db_name is None:
            db_name = config.get('db', 'database')
        self._conn = sqlite3.connect(db_name)
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params):
        self.cursor.execute(sql, params or ())
    
    def executemany(self, sql, seq_of_params):
        self.cursor.executemany(sql, seq_of_params) #sqlite has execute many i guess?

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params):
        self.cursor.execute(sql, params or ())
        return self.fetchall()
