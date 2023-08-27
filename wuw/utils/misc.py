""" Miscellaneous routines.
"""
import logging
import pprint
import re

from html import escape
from typing import TypeAlias, Any, Dict

logger = logging.getLogger(__name__)

ConfigDict: TypeAlias = Dict[str, Any]


def stringToIdentifier(s: str, white_space_becomes: str = '_') -> str:
    """ Takes a string and makes it suitable for use as an identifier.

        Translates to lower case.
        Replaces white space by the white_space_becomes character (default=underscore).
        Removes and punctuation.
    """
    s = s.lower()
    s = re.sub(r"\s+", white_space_becomes, s) # replace whitespace with underscores
    s = re.sub(r"-", "_", s) # replace hyphens with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "", s) # remove everything that's not a character, a digit or a _
    return s



def replaceEolChars(attr: str) -> str:
    """ Replace end-of-line characters with unicode glyphs so that all table rows fit on one line.
    """
    return (attr.replace('\r\n', chr(0x21B5))
            .replace('\n', chr(0x21B5))
            .replace('\r', chr(0x21B5)))

