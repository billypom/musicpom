import os
from utils.add_files_to_database import add_files_to_database
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir



def scan_for_music(progress_callback=None):
    """
    Scans for audio files in user-defined paths
    - Paths are defined in config file
    - Accepted file extensions are defined in config file
    - Adds found file to database
    """
    if progress_callback:
        progress_callback.emit('Scanning libraries...')
    config = ConfigParser()
    config.read(Path(user_config_dir(appname="musicpom", appauthor="billypom")) / "config.ini")
    libraries = [path.strip() for path in config.get("settings", "library").split(',')]
    extensions = config.get("settings", "extensions").split(",")

    # Use each library as root dir, walk the dir and find files
    for library in libraries:
        files_to_add = []
        for dirpath, _, filenames in os.walk(library):
            for file in filenames:
                filename = os.path.join(dirpath, file)
                if any(filename.lower().endswith(ext) for ext in extensions):
                    files_to_add.append(filename)
        add_files_to_database(files_to_add, progress_callback)
