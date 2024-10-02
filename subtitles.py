
import regex
import sys
from datetime import datetime
from subtitle import Subtitle
from subpair import SubPair
from suboptions import SubOptions

SENT_BOUNDARIES_REGEX = r'[\!\.\?]$'

ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}\s?'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]\s?'
MULTIPLE_SPACES = r'[\s]+'

# Greedily replace HTML
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

class Subtitles:
    """
    Subtitles is a class that takes in a body of text represent an SRT file and stores a list of subtitles associated
    with a single language. It also allows merging of sentences and aligning subtitles from another language based
    on timecodes.
    """
    def __init__(self, text, offset='00:00:00,000', offset_is_negative=False):
        # First replace bad carriage returns:
        text = regex.sub(r'\r', '', text)

        self.index = 0
        self.subtitles = []

        # Split on 2 or more lines in a row
        sub_contents = regex.split(r'\n{2,}', text)

        # Best to only parse this once, rather than in the Subtitle class
        offset = datetime.strptime(offset, Subtitle.srt_time_format)

        # We need to split subtitles if they have dashes that indicate a change in speaker
        def _split_multiple_speakers(text):
            parts = regex.split(r'(^|\n)-\s*', text)
            # Join each individual speaker's words
            joined = [part.replace("\n", " ") for part in parts]
            # return a cleaned version
            return [part.strip() for part in joined if len(part)]


        for sub_content in sub_contents:
            sub_content = sub_content.strip().split("\n")[1:]
            if len(sub_content) == 0:
                continue
            timecode_string = sub_content[0]

            # sterilize the text before we look for multiple speakers
            text = '||'.join(sub_content[1:])
            text = self.sterilize(text)
            text = text.replace('||', '\n')
            if len(text) == 0:
                continue
            individuals = _split_multiple_speakers(text)
            for individual in individuals:
                try:
                    subtitle = Subtitle(timecode_string, individual, offset, offset_is_negative)
                    if subtitle.has_content():
                        self.subtitles.append(subtitle)
                except ValueError as e:
                    sys.stderr.write(f'Value error in subtitle timestring "{sub_content[0]}": {e}\n')

        self.subtitles = self.merge_sentences()

    def sterilize(self, text):
        """
        Yes, many of these regex's could be combined for performance but at the expense of readability
        :param text: text to sterilize
        :returns: True if text length is not zero after sterilization when appropriate
        """

        # Just completely void subtitles with the musical note or leading # which indicates music
        if MUSICAL_NOTE in text or regex.match(LEADING_POUND_SIGN, text) is not None:
            return ''

        # A url invalides the entire subtitle
        if regex.search(URL_REGEX, text, regex.MULTILINE) is not None:
            return ''

        # Remove HTML content
        text = regex.sub(HTML_REGEX, '', text)

        # Strip character markers and captions
        text = regex.sub(CHARACTER_MARKER_REGEX, '', text)
        text = regex.sub(CAPITALS_REGEX, '', text)

        # Strip quoted content. There's no telling whether it's actually a character or an off-screen
        text = regex.sub(QUOTES_REGEX, '', text)

        # Remove content surrounded by parenthesis
        text = regex.sub(PARENTHESES_REGEX, "", text)

        # Remove content surrounded by curly brackets
        text = regex.sub(CURLY_BRACKET_REGEX, '', text)

        # Remove content surrounded by square brackets
        text = regex.sub(SQUARE_BRACKET_REGEX, '', text)

        # Remove leading hyphens
        text = regex.sub(LEADING_HYPHENS_REGEX, '', text)

        # Remove ellipses
        text = regex.sub(ELLIPSES_REGEX, '', text)

        # Replace multiple whitespace characters with one
        text = regex.sub(MULTIPLE_SPACES, ' ', text)

        text = text.strip()

        return text

    def merge_sentences(self):
        """
        Merges subtitles into sentences. If a subtitle does not end with a word boundary,
        the subsequent subtitles will be merged until a word boundary is found.
        :return: merged subtitles
        """
        to_delete = []
        current = None
        for sub in self.subtitles:
            if regex.search(SENT_BOUNDARIES_REGEX, sub.text):
                found_boundary = True
            else:
                # print(f'No word boundary for: {sub.text}')
                found_boundary = False
                if current is None:
                    current = sub
            if current is not None and current != sub:
                current.merge(sub)
                to_delete.append(sub)
            if found_boundary:
                current = None

        return [s for s in self.subtitles if s not in to_delete]

    def align(self, target):
        """
        Aligns the subtitles in target by iterating over the subtitles in self and looking for a match in target
        based on timecodes. The targets found might be multiple in which case the SubPair object will have one source
        and multiple sub_options. Those will be resolved in this function as well (if possible) by selecting the
        options with the greatest overlap, compared to the previous subtitle.
        :param target: Another Subtitles object for corresponding language
        :return: a list of SubPair objects
        """
        pairs = []
        previous = None
        if len(self.subtitles) == 0:
            sys.stderr.write("No subtitles" + '\n')
            exit(0)
        for sub in self:
            sub_pair = SubPair(previous, sub, target.find(sub))
            pairs.append(sub_pair)
            if previous is not None:
                previous.subsequent = sub_pair
            previous = sub_pair

        # Resolve overlaps
        resolved = []
        current = pairs[0]
        while current.subsequent is not None:
            current.resolve_conflicts()
            if not current.flagged_for_delete:
                resolved.append(current)
            current = current.subsequent
        resolved.append(current)

        for pair in resolved:
            pair.merge_options()

        return resolved

    def find(self, other):
        """
        Find the counterpart to a subtitle provided from another language in the current set
        :param other: a target subtitle to find the match
        :return: counterpart subtitle or None
        """

        options = []
        for current in self.subtitles:
            if current.end < other.start:
                continue
            elif current.start > other.end:
                break
            else:
                options.append(current)
        return SubOptions(options)

    @staticmethod
    def _find_best(source, options):
        """
        If more than one subtitle was found, select the one with the largest overlap
        :returns: option with the largest overlap with source subtitle
        """
        overlap = 0
        best = None
        for option in options:
            _overlap = source.overlap(option)
            if _overlap > overlap:
                overlap = _overlap
                best = option
        return best

    def __iter__(self):
        self.index = -1
        if len(self.subtitles):
            self.current = self.subtitles[self.index]
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.subtitles):
            self.current = self.subtitles[self.index]
            return self.current
        else:
            raise StopIteration
