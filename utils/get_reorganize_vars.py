from mutagen.id3 import ID3


def get_reorganize_vars(filepath: str) -> tuple[str, str]:
    """
    Takes in a path to an audio file
    returns the (artist, album) as a tuple of strings

    if no artist or album or ID3 tags at all are found,
    function will return ("Unknown Artist", "Unknown Album")
    """
    # TODO: fix this func. id3_remap(get_tags())
    # or is what i have less memory so more better? :shrug:
    audio = ID3(filepath)
    try:
        artist = str(audio["TPE1"].text[0])
        if artist == "":
            artist = "Unknown Artist"
    except KeyError:
        artist = "Unknown Artist"

    try:
        album = str(audio["TALB"].text[0])
        if album == "":
            album = "Unknown Album"
    except KeyError:
        album = "Unknown Album"

    return artist, album
