import re
from typing import Tuple
from mutagen.id3._frames import TYER, TDAT


def convert_date_str_to_tyer_tdat_id3_tag(date_str) -> Tuple:
    """
    Handles date formatting when updating a date record in the music table
    Date string format = YYYY-MM-DD
    """
    if not date_str:
        return None, None
    match = re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", date_str)
    if not match:
        raise ValueError("Invalid date format")
    # print(f"convert_date_str_to_tyer_tdat_id3_tag(): match: {match}")
    year, month, day = match.groups()
    # print(
    #     f"convert_date_str_to_tyer_tdat_id3_tag(): month: {month} | day: {day} | year: {year}"
    # )
    # only year
    if not month or not day:
        # print(TYER(encoding=3, text=year))
        return TYER(encoding=3, text=year), None
    else:
        date_value = f"{day}{month}"
        # print(TYER(encoding=3, text=year), TDAT(encoding=3, text=date_value))
        return TYER(encoding=3, text=year), TDAT(encoding=3, text=date_value)
