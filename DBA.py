import sqlite3
import logging
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir


class DBAccess:
    def __init__(self, db_name=None):
        logging.info("Instantiating DBAccess")
        config = ConfigParser()
        cfg_file = (
            Path(user_config_dir(appname="musicpom", appauthor="billypom"))
            / "config.ini"
        )
        config.read(cfg_file)
        if db_name is None:
            db_name = config.get("settings", "db")
        self._conn: sqlite3.Connection = sqlite3.connect(db_name)
        self._cursor: sqlite3.Cursor = self._conn.cursor()

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
        self.cursor.executemany(sql, seq_of_params)  # sqlite has execute many i guess?

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params):
        self.cursor.execute(sql, params or ())
        return self.fetchall()
