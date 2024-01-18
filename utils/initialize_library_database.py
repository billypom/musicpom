import DBA

def initialize_library_database():
    with open('utils/create_library.sql', 'r') as file:
        lines = file.read()
        for statement in lines.split(';'):
            print(f'executing [{statement}]')
            with DBA.DBAccess() as db:
                db.execute(statement, ())