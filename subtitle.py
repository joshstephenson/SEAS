import regex
from helpers import parse_timestring
import sys

TIMECODE_SEPARATOR = ' --> '
TIMECODE_LINE_REGEX = r'(\d{2}:\d{2}:\d{2},\d{3}).+(\d{2}:\d{2}:\d{2},\d{3})'


class Subtitle:
    """
    Subtitle represents a single visual text element in a movie in just one language
    """

    def __init__(self, timestring, text, offset, offset_is_negative=False):
        self.offset = offset
        self.offset_is_negative = offset_is_negative

        # join multiple lines of text into one line if necessary
        self.text = text if type(text) is str else " ".join(text).strip()

        # Used to display subtitle timecodes
        self.timestring = timestring

        # Used to compare subtitle timecodes
        self.start = 0
        self.end = 0

        # Parse the time code into a number of milliseconds since the start
        self.parse_time_codes(offset, offset_is_negative)

        # Can be set externally
        self.previous = None
        self.following = None

    def has_content(self):
        # return regex.match(r'[[:lower:]]{2,}', self.text) is not None
        # Count the number of lowercase and uppercase letters in the string
        lower_count = sum(1 for char in self.text if char.islower())
        upper_count = sum(1 for char in self.text if char.isupper())

        # The string must be either:
        # - More than one lowercase character, or
        # - One lowercase and one uppercase character
        return (lower_count > 1) or (lower_count >= 1 and upper_count >= 1)

    def parse_time_codes(self, offset, offset_is_negative):
        """
        Turn timestrings like '01:23:45,678' into an integer offset milliseconds since movie start
        :param offset: offset is a datetime object
        :param offset_is_negative: boolean to indicate whether above offset is negative
        :return: an integer duration since video start
        """

        match = regex.match(TIMECODE_LINE_REGEX, self.timestring.strip())
        if match is not None and len(match.groups()) > 1:
            self.start = parse_timestring(match.group(1), offset, offset_is_negative)
            self.end = parse_timestring(match.group(2), offset, offset_is_negative)
            self.timestring = f'{match.group(1)} --> {match.group(2)}'
        else:
            sys.stderr.write("Invalid timecode string: " + self.timestring + "\n")
            # Nullify this subtitle
            self.text = ''

    def overlap(self, other):
        """
        Find the duration of time two subtitles overlap with each other
        :param other: the other subtitle to compare with self
        :return: duration of time two subtitles overlap with each other
        """
        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return end - start

    def merge(self, other):
        """
        Merge another subtitle with this subtitle. Used when a sentence is spread across multiple subtitles.
        :param other: other subtitle to merge
        """
        self.text += " " + other.text
        self.end = other.end
        self.timestring = self.timestring.split(TIMECODE_SEPARATOR)[0] + TIMECODE_SEPARATOR + \
                          other.timestring.split(TIMECODE_SEPARATOR)[1]

    def __str__(self):
        return self.text

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.timestring == other.timestring

    def __hash__(self):
        return hash(self.timestring)
