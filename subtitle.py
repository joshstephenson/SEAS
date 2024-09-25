import regex
from datetime import datetime

SRT_TIME_FORMAT = '%H:%M:%S,%f'
TIMECODE_SEPARATOR = ' --> '
ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}\s?'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]\s?'
MULTIPLE_SPACES = r'[\s]+'
# HTML_REGEX = r'<[^<]+?>' # This only strips the tags
HTML_REGEX = r'<.*?>.*?</.*?>'
QUOTES_REGEX = r'(["“”«»„‟‹›〝〞『』【】「」])(.*?)(["“”«»„‟‹›〝〞『』【】「」])' #r'"[^"]+?"'

# Character marker might look like:
# JOHN: blah blah
# OR
# Person #1: blah blah
# allows up to three 'words' before a colon and space
CHARACTER_MARKER_REGEX = r'^([\w.,#\'-]+\s?){1,3}: '

# Matches 2 or more words in all CAPS along with adjacent punctuation
# CAPITALS_REGEX = r'([A-Z]{2,}[,:.]?\s){2,}[:]?'
CAPITALS_REGEX = r'[A-Z,]{2,}( [A-Z,]{2,})+'
PARENTHESES_REGEX = r'\(.*\)'
LEADING_HYPHENS_REGEX = r'^-'

# Used to transcribe music
MUSICAL_NOTE = '♪'
LEADING_POUND_SIGN = r'^#'

class Subtitle:
    """
    Subtitle represents a single visual text element in a movie in just one language
    """
    srt_time_format = SRT_TIME_FORMAT

    def __init__(self, timestring, text, sterilize, offset, offset_is_negative):
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

        # remember if we have sterilized so we don't do it again
        self.sterilized = False

        self.sterilize(sterilize)

    def sterilize(self, sterilize):
        """
        :param sterilize: boolean to strip HTML and special characters
        :returns: True if text length is not zero after sterilizaton when appropriate
        """

        # Just completely void subtitles with the musical note
        # A better option would be to strip content between musical notes
        # and strip lines that start with a musical not, but I think this is probably sufficient
        if MUSICAL_NOTE in self.text or regex.match(LEADING_POUND_SIGN, self.text) is not None:
            self.text = ''
            return

        self.text = self.text.replace('\n', ' ')

        if sterilize and not self.sterilized:
            self.text = regex.sub(r'\r', '', self.text)
            # Strip character markers and captions
            self.text = regex.sub(CHARACTER_MARKER_REGEX, '', self.text)
            self.text = regex.sub(CAPITALS_REGEX, '', self.text)

            # Strip quoted content. There's no telling whether it's actually a character or an off-screen
            self.text = regex.sub(QUOTES_REGEX, '', self.text)

            # Remove content surrounded by parenthesis
            self.text = regex.sub(PARENTHESES_REGEX, "", self.text)

            # Remove HTML content
            self.text = regex.sub(HTML_REGEX, '', self.text)

            # Remove content surrounded by curly brackets
            self.text = regex.sub(CURLY_BRACKET_REGEX, '', self.text)

            # Remove content surrounded by square brackets
            self.text = regex.sub(SQUARE_BRACKET_REGEX, '', self.text)

            # Remove leading hyphens
            self.text = regex.sub(LEADING_HYPHENS_REGEX, '', self.text)

            # Remove ellipses
            self.text = regex.sub(ELLIPSES_REGEX, '', self.text)

            # Replace multiple whitespace characters with one
            self.text = regex.sub(MULTIPLE_SPACES, ' ', self.text)

            self.text = self.text.strip()

            self.sterilized = True

    def has_content(self):
        return len(self.text) > 0

    def parse_time_codes(self, offset, offset_is_negative):
        """
        Turn timestrings like '01:23:45,678' into an integer offset milliseconds since movie start
        :param offset: offset is a datetime object
        :param offset_is_negative: boolean to indicate whether above offset is negative
        :return: an integer duration since video start
        """

        def _parse_timestring(timestring):
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

        parts = self.timestring.split(TIMECODE_SEPARATOR)
        self.start = _parse_timestring(parts[0])
        self.end = _parse_timestring(parts[1])

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
