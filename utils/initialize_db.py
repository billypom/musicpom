import DBA


def initialize_db():
    """Recreates everything in the database"""
    with open("utils/init.sql", "r") as file:
        lines = file.read()
        for statement in lines.split(";"):
            print(f"executing [{statement}]")
            with DBA.DBAccess() as db:
                db.execute(statement, ())
