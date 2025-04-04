from logging import debug, warning, error
from mutagen.id3 import ID3
from traceback import print_exc, format_exc
from sys import exc_info


def delete_album_art(file: str) -> bool:
    """Deletes the album art (APIC tag) for a specific song

    Args:
        `file`: fully qualified path to an audio file

    Returns:
        True on success, False on failure
    """
    try:
        audio = ID3(file)
        debug(audio)
        if "APIC:" in audio:
            del audio["APIC:"]
            debug("Deleting album art")
            audio.save()
        else:
            warning("delete_album_art_for_current_song() | no tag called APIC")
        return True
    except Exception:
        print_exc()
        exctype, value = exc_info()[:2]
        error(
            f"delete_album_art_for_current_song() | Error processing this file:\t {file}\n{exctype}\n{value}\n{format_exc()}"
        )
        return False
