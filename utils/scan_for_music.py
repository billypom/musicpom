import os
import DBA
from configparser import ConfigParser
from utils import add_files_to_library, get_id3_tags
from utils import safe_get

config = ConfigParser()
config.read("config.ini")


def scan_for_music():
    root_dir = config.get("directories", "library")

    # for dirpath, dirnames, filenames ...
    for _, _, filenames in os.walk(root_dir):
        add_files_to_library(filenames)
