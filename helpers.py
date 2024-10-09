import regex
import sys
from datetime import datetime

ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}\s?'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]\s?'
MULTIPLE_SPACES = r'[\s]+'

# We only want to replace the italics tags, not the text inside
ITALICS_REGEX = r'</?[iI]>'
# But for all other HTML we want to strip everything inside too
HTML_REGEX = r'<.*>'
QUOTES_REGEX = r'(["“”«»„‟‹›〝〞『』【】「」])(.*?)(["“”«»„‟‹›〝〞『』【】「」])' #r'"[^"]+?"'

# Character marker might look like:
# JOHN: blah blah
# OR
# Person #1: blah blah
# allows up to three 'words' before a colon and space
CHARACTER_MARKER_REGEX = r'^([\w.,#\'-]+\s?){1,3}: '

# Matches 2 or more words in all CAPS along with adjacent punctuation
# CAPITALS_REGEX = r'([A-Z]{2,}[,:.]?\s){2,}[:]?'
CAPITALS_REGEX = r'[A-Z,]{2,}( [A-Z0-9,]{2,})+'
PARENTHESES_REGEX = r'\(.*\)'
LEADING_HYPHENS_REGEX = r'^-'

# Used to transcribe music
MUSICAL_NOTE = '♪'
LEADING_POUND_SIGN = r'^#'

URL_REGEX = r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'

SRT_TIME_FORMAT = '%H:%M:%S,%f'

def sterilize(text):
    """
    :param text: text to sterilize
    :returns: sterilized text
    """

    # Completely invalidate subtitles with the musical notes, leading # or URLs
    if MUSICAL_NOTE in text or regex.match(LEADING_POUND_SIGN, text) is not None or regex.search(URL_REGEX, text, regex.MULTILINE) is not None:
        return ''

    # Multiple words in all caps are no good
    text = regex.sub(CAPITALS_REGEX, '', text)

    # First strip italics tags
    text = regex.sub(ITALICS_REGEX, '', text)

    # Then remove all other HTML with inner content
    text = regex.sub(HTML_REGEX, '', text)

    # Strip character markers and captions
    text = regex.sub(CHARACTER_MARKER_REGEX, '', text)
    text = regex.sub(CAPITALS_REGEX, '', text)

    # Strip quoted content. There's no telling whether it's actually a character or an off-screen
    # Not sure we should be stripping quotes afterall. They're used for when characters are quoting things.
    # text = regex.sub(QUOTES_REGEX, '', text)

    # Remove content surrounded by parenthesis
    text = regex.sub(PARENTHESES_REGEX, "", text)

    # Remove content surrounded by curly brackets
    text = regex.sub(CURLY_BRACKET_REGEX, '', text)

    # Remove content surrounded by square brackets
    text = regex.sub(SQUARE_BRACKET_REGEX, '', text)

    # Remove leading hyphens
    text = regex.sub(LEADING_HYPHENS_REGEX, '', text)

    # Remove ellipses
    # text = regex.sub(ELLIPSES_REGEX, '', text)

    # Replace multiple whitespace characters with one
    text = regex.sub(MULTIPLE_SPACES, ' ', text)

    text = text.strip()

    return text


def get_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as e:
        sys.stderr.write(f'UTF-8 decoding failed. Will try latin-1 encoding.' + '\n')
        with open(filename, 'r', encoding='latin-1') as source_file:
            srt_text = source_file.read()
    return srt_text


def parse_timestring(timestring, offset='00:00:00,000', offset_is_negative=False):
    pt = datetime.strptime(timestring, SRT_TIME_FORMAT)
    if offset_is_negative:
        microsecond = pt.microsecond - offset.microsecond
        second = pt.second - offset.second
        minute = pt.minute - offset.minute
        hour = pt.hour - offset.hour
    else:
        microsecond = pt.microsecond + offset.microsecond
        second = pt.second + offset.second
        minute = pt.minute + offset.minute
        hour = pt.hour + offset.hour
    return microsecond + (second + minute * 60 + hour * 3600) * 1000000
