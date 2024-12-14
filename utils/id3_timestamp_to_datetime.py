import datetime
from mutagen.id3._specs import ID3TimeStamp


def id3_timestamp_to_datetime(timestamp: ID3TimeStamp):
    """Turns a mutagen ID3TimeStamp into a format that SQLite can use for Date field"""
    if len(timestamp.text) == 4:  # If only year is provided
        datetime_obj = datetime.datetime.strptime(timestamp.text, '%Y')
    else:
        try:
            datetime_obj = datetime.datetime.strptime(timestamp.text, '%Y-%m-%d')
        except ValueError:
            datetime_obj = datetime.datetime.strptime(timestamp.text, '%Y%m%d')
    return datetime_obj.strftime('%Y-%m-%d')
