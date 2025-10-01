import os
from PyQt5.QtCore import QThreadPool
import DBA
import logging
from utils import get_reorganize_vars, Worker

def export_playlist_by_id(playlist_db_id: int) -> bool:
    """
    Exports a playlist to its defined auto_export_path, by database ID
    """
    threadpool = QThreadPool()
    try:
        with DBA.DBAccess() as db:
            result = db.query('''
                        SELECT auto_export_path, path_prefix FROM playlist WHERE id = ?
                        ''', (playlist_db_id,)
                        )
            auto_export_path = result[0][0]
            path_prefix = result[0][1]
    except Exception as e:
        logging.error(
            f"export_playlist_by_id.py | Could not contact database: {e}"
        )
        return False

    # If the prefix is null, then use an empty string
    if not path_prefix:
        path_prefix = ""

    # If the path is nothing, just stop
    if not auto_export_path:
        return False

    # Get filepaths for selected playlist from the database
    try:
        with DBA.DBAccess() as db:
            data = db.query(
                """SELECT s.filepath FROM song_playlist as sp
                JOIN song as s ON s.id = sp.song_id
                WHERE sp.playlist_id = ?;""",
                (playlist_db_id,),
            )
            db_paths = [path[0] for path in data]
    except Exception as e:
        logging.error(
            f"export_playlist_by_id.py | Could not retrieve records from playlist: {e}"
        )
        return False

    # Gather playlist song paths
    write_paths = []
    # Relative paths
    for song in db_paths:
        artist, album = get_reorganize_vars(song)
        write_path = os.path.join(
            path_prefix, artist, album, song.split("/")[-1] + "\n"
        )
        write_paths.append(str(write_path))


    worker = Worker(write_to_playlist_file, write_paths, auto_export_path)
    # worker.signals.signal_finished.connect(None)
    # worker.signals.signal_progress.connect()
    threadpool.start(worker)
    return True

def write_to_playlist_file(paths: list[str], outfile: str, progress_callback=None) -> None:
    """
    Writes a list of strings to a m3u file
    """
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w") as f:
        f.writelines(paths)
