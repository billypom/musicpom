import DBA
from components.ErrorDialog import ErrorDialog


def delete_song_id_from_database(song_id: int):
    """
    Handles deleting a song from the database by ID
    Accounts for playlists and other dependencies

    Returns True on success
    False on failure/error
    """
    try:
        with DBA.DBAccess() as db:
            db.execute("DELETE FROM song_playlist WHERE song_id = ?", (song_id,))
            db.execute("DELETE FROM song WHERE id = ?", (song_id,))
    except Exception as e:
        dialog = ErrorDialog(
            f"delete_song_id_from_database.py | could not delete song id {song_id} from database: {e}"
        )
        dialog.exec_()
        return False
    return True
