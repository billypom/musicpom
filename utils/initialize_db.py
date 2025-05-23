import DBA
from logging import debug


def initialize_db():
    """Recreates everything in the database"""
    with DBA.DBAccess() as db:
        with open("utils/init.sql", "r") as file:
            lines = file.read()
            for statement in lines.split(";"):
                debug(f"executing [{statement}]")
                #with DBA.DBAccess() as db: # is this better?
                db.execute(statement, ())
