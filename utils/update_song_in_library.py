import DBA
from components.ErrorDialog import ErrorDialog


def update_song_in_library(library_id: int, edited_column_name: str, user_input_data: str):
    """Updates a field in the library database based on an ID

    Args:
        library_id: the database ID of the song
        edited_column_name: the name of the database column
        user_input_data: the data to input

    Returns:
        True or False"""
    try:
        with DBA.DBAccess() as db:
            # yeah yeah this is bad... the column names are defined in the program by me so im ok with it because it works
            db.execute(f'UPDATE library SET {edited_column_name} = ? WHERE id = ?', (user_input_data, library_id))
    except Exception as e:
        dialog = ErrorDialog(f'Unable to update [{edited_column_name}] to [{user_input_data}]. ID: {library_id} | {e}')
        dialog.exec_()
        return False
    return True

