from datetime import datetime
from typing import Optional

import regex
from nltk import sent_tokenize
import sys

TIMECODE_SEPARATOR = ' --> '
TIMECODE_LINE_REGEX = r'(\d{2}:\d{2}:\d{2},\d{3}).+(\d{2}:\d{2}:\d{2},\d{3})'
SRT_TIME_FORMAT = '%H:%M:%S,%f'


def parse_timestring(timestring, offset='00:00:00,000', offset_is_negative=False):
    if isinstance(offset, str):
        offset = datetime.strptime(offset, SRT_TIME_FORMAT)
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


def _parse_time_codes(timestring) -> (int, int, str):
    """
    Turn timestrings like '01:23:45,678' into an integer offset milliseconds since movie start
    :return: an integer duration since video start
    """

    match = regex.match(TIMECODE_LINE_REGEX, timestring.strip())
    if match is not None and len(match.groups()) > 1:
        start = parse_timestring(match.group(1))
        end = parse_timestring(match.group(2))
        timestring = f'{match.group(1)} --> {match.group(2)}'
        return start, end, timestring
    else:
        sys.stderr.write("Invalid timecode string: " + timestring + "\n")
        # Nullify this subtitle
        return None


ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}\s?'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]\s?'
MULTIPLE_SPACES = r'[\s]+'

# We only want to replace the italics tags, not the text inside
ITALICS_REGEX = r'</?[iI]>'
# But for all other HTML we want to strip everything inside too
HTML_REGEX = r'<.*>'
QUOTES_REGEX = r'(["“”«»„‟‹›〝〞『』【】「」])(.*?)(["“”«»„‟‹›〝〞『』【】「」])'  # r'"[^"]+?"'

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

# URL_REGEX = r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'
URL_REGEX = r'((http|https)\:\/\/)?[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'


def sterilize(sub_lines: [str]) -> Optional[str]:
    """
    :param sub_lines: lines of text to sterilize
    :returns: sterilized text
    """
    text = '||'.join(sub_lines)
    if len(text) == 0:
        return None
    # Completely invalidate subtitles with the musical notes, leading # or URLs
    test1 = MUSICAL_NOTE in text
    test2 = regex.match(LEADING_POUND_SIGN, text) is not None
    test3 = regex.search(URL_REGEX, text, regex.MULTILINE) is not None
    if test1 or test2 or test3:
        return None

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
    # Not sure if we should be stripping quotes after all. They're used for when characters are quoting things.
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

    return text.replace('||', '\n')


class Subtitle:
    """
    Subtitle represents a single visual text element in a movie in just one language
    """

    def __init__(self, lines, is_source=True):
        def _sterilize_and_split(sub_text: [str]):
            text = sterilize(sub_text)
            return _split_multiple_speakers(text) if text is not None else None

        def _split_multiple_speakers(sub_text):
            # multiple speakers are demarcated with hyphen at the beginning of a line:
            # - I was home all night.
            # - I don't believe you.
            _parts = regex.split(r'(^|\n)-\s*', sub_text)
            # Join each individual speaker's words
            joined = [part.replace("\n", " ") for part in _parts]
            # return a cleaned version
            untokenized = [part.strip() for part in joined if len(part)]
            return [s.strip() for u in untokenized for s in sent_tokenize(u)]  # TODO: add other language support

        # subtitles have a many-to-many relationship with utterances
        self.utterances = set()

        # Can be set externally
        self.previous = None
        self.subsequent = None

        self.is_source = is_source
        self.lines = lines
        parts = self.lines.split('\n')

        self.index = int(parts[0].replace('\ufeff', '')) # stripping BOM mark
        self.start, self.end, self.timestring = _parse_time_codes(parts[1])
        self.texts = _sterilize_and_split(parts[2:])
        if self.texts is None:
            self.texts = ['']
        self.text = " ".join(self.texts)

    def linked_via_utterance(self):
        """
        returns subtitles linked via utterances
        """
        adjacent = []
        for utterance in self.utterances:
            adjacent.extend([s for s in utterance.subtitles if s != self])
        return adjacent

    def has_content(self):
        self.text = self.text.strip()
        # return regex.match(r'[[:lower:]]{2,}', self.text) is not None
        # Count the number of lowercase and uppercase letters in the string
        lower_count = sum(1 for char in self.text if char.islower())
        upper_count = sum(1 for char in self.text if char.isupper())

        # The string must be either:
        # - More than one lowercase character, or
        # - One lowercase and one uppercase character
        return (lower_count > 1) or (lower_count >= 1 and upper_count >= 1)

    def __str__(self):
        return self.lines

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.timestring == other.timestring

    def __hash__(self):
        return hash(self.timestring)
