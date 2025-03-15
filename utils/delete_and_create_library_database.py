import DBA
from logging import debug


def delete_and_create_library_database():
    """Clears all songs in database"""
    with open("utils/delete_and_create_library.sql", "r") as file:
        lines = file.read()
        for statement in lines.split(";"):
            debug(f"executing [{statement}]")
            with DBA.DBAccess() as db:
                db.execute(statement, ())
