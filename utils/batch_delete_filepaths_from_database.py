import DBA
import logging
from components.ErrorDialog import ErrorDialog


def batch_delete_filepaths_from_database(
    files: list[str], chunk_size=1000, progress_callback=None
) -> bool:
    """
    Handles deleting many songs from the database by filepath
    Accounts for playlists and other song-linked tables
    Args:
        files: a list of absolute filepaths to songs
        chunk_size: how many files to process at once in DB
        progress_callback: emit this signal for user feedback

    Returns True on success
    False on failure/error
    """
    # Get song IDs from filepaths
    try:
        with DBA.DBAccess() as db:
            placeholders = ", ".join("?" for _ in files)
            query = f"SELECT id FROM song WHERE filepath in ({placeholders});"
            result = db.query(query, files)
            song_ids = [item[0] for item in result]
    except Exception as e:
        logging.error(
            f"batch_delete_filepaths_from_database.py | An error occurred during retrieval of song_ids: {e}"
        )
        dialog = ErrorDialog(
            f"batch_delete_filepaths_from_database.py | An error occurred during retrieval of song_ids: {e}"
        )
        dialog.exec_()
        return False
    try:
        with DBA.DBAccess() as db:
            # Batch delete in chunks
            for i in range(0, len(song_ids), chunk_size):
                chunk = song_ids[i : i + chunk_size]
                placeholders = ", ".join("?" for _ in chunk)

                # Delete from playlists
                query = f"DELETE FROM song_playlist WHERE song_id IN ({placeholders});"
                db.execute(query, chunk)

                # Delete from library
                query = f"DELETE FROM song WHERE id in ({placeholders});"
                db.execute(query, chunk)
                if progress_callback:
                    progress_callback.emit(f"Deleting songs: {i}")

    except Exception as e:
        logging.error(
            f"batch_delete_filepaths_from_database.py | An error occurred during batch processing: {e}"
        )
        dialog = ErrorDialog(
            f"batch_delete_filepaths_from_database.py | An error occurred during batch processing: {e}"
        )
        dialog.exec_()
        return False
    return True
