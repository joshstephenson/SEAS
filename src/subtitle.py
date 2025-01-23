import string
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional

import regex
from nltk import sent_tokenize
import sys

from src.config import Config
from src.languages import Languages

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


def microseconds_to_string(microseconds):
    milliseconds = int((microseconds / 1e3) % 1e3)
    seconds = int((microseconds / 1e6) % 60)
    minutes = int((microseconds / (1e6 * 60)) % 60)
    hours = int((microseconds / (1e6 * 60 * 60)) % 24)

    hours = str(hours).rjust(2, '0')
    minutes = str(minutes).rjust(2, '0')
    seconds = str(seconds).rjust(2, '0')
    milliseconds = str(milliseconds).rjust(3, '0')
    return f'{hours}:{minutes}:{seconds},{milliseconds}'


ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}\s?'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]\s?'
MULTIPLE_SPACES = r'[\s]+'

# We only want to replace the italics tags, not the text inside
# ITALICS_OR_BOLD_REGEX = r'</?[iIbB]>'
ITALICS_OR_BOLD_REGEX = r'</?(i|b|font(?: color=\"[^\"]*\")?)>'
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
# \p{Lu} is unicode for uppercase. Will match accented characters.
CAPITALS_REGEX = r'[\p{Lu},]{2,}( [\p{Lu}0-9,]{2,})+'
PARENTHESES_REGEX = r'\(.*\)'
CHANGE_OF_SPEAKER_REGEX = r'([!?.])\s*(-)\s*(\p{Lu})'
LEADING_HYPHENS_REGEX = r'\A-\s?'

# Used to transcribe music
MUSICAL_NOTE = r'[♪♫♬🎵]'
LEADING_POUND_SIGN = r'^#'

# URL_REGEX = r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'
URL_REGEX = r'((http|https)\:\/\/)?[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'

MULTIPLE_ADJACENT_SPACES_REGEX = r' {2,}'
OTHER_CHARS_TO_STRIP = r'[…*]'


def sterilize(sub_lines: [str]) -> Optional[str]:
    """
    :param sub_lines: lines of text to sterilize
    :returns: sterilized text
    """
    text = '||'.join(sub_lines)
    if len(text) == 0:
        return ''
    # Completely invalidate subtitles with the musical notes, leading # or URLs
    if regex.search(MUSICAL_NOTE, text) is not None:
        return ''
    if regex.search(LEADING_POUND_SIGN, text) is not None:
        return ''
    if regex.search(URL_REGEX, text, regex.MULTILINE) is not None:
        return ''

    # Remove content surrounded by curly brackets
    text = regex.sub(CURLY_BRACKET_REGEX, '', text)

    # Remove content surrounded by square brackets
    text = regex.sub(SQUARE_BRACKET_REGEX, '', text)

    # Multiple words in all caps are no good
    text = regex.sub(CAPITALS_REGEX, '', text)

    # First strip italic and bold tags
    text = regex.sub(ITALICS_OR_BOLD_REGEX, '', text)

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

    # Remove leading hyphens
    # text = regex.sub(LEADING_HYPHENS_REGEX, '', text)
    text = regex.sub(CHANGE_OF_SPEAKER_REGEX, r"\1\n\2 \3", text)

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

    def __init__(self, lines, language, is_source=True, should_sterilize=Config.Sterilize,
                 find_sentence_boundaries=True):
        """
        :param lines: the raw lines of subtitles. The first line is index, second is timestamps and the rest are the
        content
        :param is_source: is the source or target of the subtitles for alignment
        :param should_sterilize: to sterilize subtitle contents
        """

        def _sterilize_and_split(sub_text: [str]):
            text = sterilize(sub_text)
            return _split_multiple_speakers(text) if text is not None else None

        def _split_multiple_speakers(sub_text):
            # multiple speakers are demarcated with hyphen at the beginning of a line:
            # - I was home all night.
            # - I don't believe you.
            _parts = regex.split(r'(^|\n)[-*]\s*', sub_text)
            # Join each individual speaker's words
            joined = [part.replace("\n", " ") for part in _parts]
            # return a cleaned version
            untokenized = [part.strip() for part in joined if len(part)]
            return [regex.sub(LEADING_HYPHENS_REGEX, '', s).strip() for u in untokenized for s in
                    sent_tokenize(u, self.language)]

        # subtitles have a many-to-many relationship with utterances
        self.utterances = set()

        # Can be set externally
        self.previous = None
        self.subsequent = None

        self.language = Languages.get_language_name(language)
        self.is_source = is_source
        self.lines = lines

        parts = self.lines.split('\n')
        if len(parts[0]) > 0:
            self.index = int(parts[0])
        else:
            print(len(parts[0]))
            print(parts[0].isdigit())
            raise Exception(f'Invalid subtitle: {self.lines}')
        self.start, self.end, self.timestring = _parse_time_codes(parts[1])
        if should_sterilize:

            if find_sentence_boundaries:
                self.texts = _sterilize_and_split(parts[2:])
                if self.texts is None:
                    self.texts = ['']
                else:
                    # more data stripping
                    self.text = regex.sub(MULTIPLE_ADJACENT_SPACES_REGEX, ' ', ' '.join(self.texts))
                    self.text = regex.sub(OTHER_CHARS_TO_STRIP, '', self.text)
            else:
                self.text = sterilize(parts[2:])
        else:
            if find_sentence_boundaries:
                self.texts = _split_multiple_speakers('\n'.join(parts[2:]))
                self.text = ' '.join(self.texts)
            else:
                self.text = '\n'.join(self.lines.split('\n')[2:])
                self.texts = [self.text]

    def linked_via_utterance(self):
        """
        returns subtitles linked via utterances
        """
        adjacent = []
        for utterance in self.utterances:
            adjacent.extend([s for s in utterance.subtitles if s != self])
        return adjacent

    def has_content(self):
        if self.text is None:
            return False
        text = self.text.translate(str.maketrans('', '', string.punctuation)).replace(' ', '')
        # return regex.match(r'[[:lower:]]{2,}', self.text) is not None
        # Count the number of lowercase and uppercase letters in the string
        lower_count = sum(1 for char in text if char.islower())
        upper_count = sum(1 for char in text if char.isupper())

        # The string must be either:
        # - More than one lowercase character, or
        # - One lowercase and one uppercase character
        return (lower_count > 1) or (lower_count >= 1 and upper_count >= 1)

    def delay_timecodes(self, offset):
        """
        :param offset: offset in microseconds
        """
        self.start = self.start + offset
        self.end = self.end + offset
        self.timestring = f'{microseconds_to_string(self.start)}{TIMECODE_SEPARATOR}{microseconds_to_string(self.end)}'
        lines = self.lines.split('\n')
        lines[1] = self.timestring
        self.lines = '\n'.join(lines)

    def overlap(self, other: "Subtitle"):
        """
        Find the duration of time two subtitles overlap with each other
        :param other: the other subtitle to compare with self
        :return: duration of time two subtitles overlap with each other
        """
        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return end - start

    def __str__(self):
        return self.lines

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.timestring == other.timestring

    def __hash__(self):
        return hash(self.timestring)
