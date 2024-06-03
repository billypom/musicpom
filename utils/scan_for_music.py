import os
from configparser import ConfigParser
from utils import add_files_to_library

config = ConfigParser()
config.read("config.ini")


def scan_for_music():
    root_dir = config.get("directories", "library")
    # for dirpath, dirnames, filenames ...
    for _, _, filenames in os.walk(root_dir):
        add_files_to_library(filenames)
