import os
from PyQt5.QtCore import pyqtSignal
from utils.add_files_to_library import add_files_to_library
from configparser import ConfigParser
from pathlib import Path
from appdirs import user_config_dir



def scan_for_music():
    config = ConfigParser()
    cfg_file = (
        Path(user_config_dir(appname="musicpom", appauthor="billypom")) / "config.ini"
    )
    config.read(cfg_file)
    root_dir = config.get("directories", "library")
    extensions = config.get("settings", "extensions").split(",")
    files_to_add = []
    # for dirpath, dirnames, filenames ...
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            filename = os.path.join(dirpath, file)
            if any(filename.lower().endswith(ext) for ext in extensions):
                files_to_add.append(filename)
    add_files_to_library(files_to_add)
