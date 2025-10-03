from logging import debug, error, warning
from components import ErrorDialog
from components.HeaderTags import HeaderTags2
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError
from mutagen.id3._frames import USLT, Frame

def set_tag(filepath: str, db_column: str, value: str):
    """
    Sets the ID3 tag for a file given a filepath, db_column, and a value for the tag

    Args:
        filepath: path to the mp3 file
        db_column: db column name of the ID3 tag
        value: value to set for the tag

    Returns:
        True / False
    """
    headers = HeaderTags2()
    debug(f"filepath: {filepath} | db_column: {db_column} | value: {value}")

    try:
        try:  # Load existing tags
            audio_file = ID3(filepath)
        except ID3NoHeaderError:  # Create new tags if none exist
            audio_file = ID3()
        # Lyrics get handled differently
        if db_column == "lyrics":
            try:
                audio = ID3(filepath)
            except Exception as e:
                error(f"ran into an exception: {e}")
                audio = ID3()
            audio.delall("USLT")
            frame = USLT(encoding=3, text=value)
            audio.add(frame)
            audio.save()
            return True
        # DB Tag into Mutagen Frame Class
        if db_column in headers.db:
            frame_class = headers.db[db_column].frame_class
            assert frame_class is not None # ooo scary
            if issubclass(frame_class, Frame):
                frame = frame_class(encoding=3, text=[value])
                audio_file.add(frame)
        else:
            warning(f'Tag "{db_column}" not found - ID3 tag update skipped')
        audio_file.save(filepath)
        return True
    except Exception as e:
        dialog = ErrorDialog(f"set_tag.py | An unhandled exception occurred:\n{e}")
        dialog.exec_()
        return False
