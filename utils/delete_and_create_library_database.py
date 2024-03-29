import DBA

def delete_and_create_library_database():
    with open('utils/delete_and_create_library.sql', 'r') as file:
        lines = file.read()
        for statement in lines.split(';'):
            print(f'executing [{statement}]')
            with DBA.DBAccess() as db:
                db.execute(statement, ())
