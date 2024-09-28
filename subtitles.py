
import regex
import sys
from datetime import datetime
from subtitle import Subtitle
from subpair import SubPair
from suboptions import SubOptions

SENT_BOUNDARIES_REGEX = r'[\!\.\?]$'

class Subtitles:
    """
    Subtitles is a class that takes in a body of text represent an SRT file and stores a list of subtitles associated
    with a single language. It also allows merging of sentences and aligning subtitles from another language based
    on timecodes.
    """
    def __init__(self, text, sterilize=True, offset='00:00:00,000', offset_is_negative=False):
        # First replace bad carriage returns:
        text = regex.sub(r'\r', '', text)

        self.index = 0
        self.subtitles = []

        # Split on 2 or more lines in a row
        sub_contents = regex.split(r'\n{2,}', text)

        # Best to only parse this once, rather than in the Subtitle class
        offset = datetime.strptime(offset, Subtitle.srt_time_format)

        # We need to split subtitles if they have dashes that indicate a change in speaker
        def _split_multiple_speakers(lines):
            joined = " ".join(sub_content[1:])
            return regex.split(r'-\s*', joined)


        for sub_content in sub_contents:
            sub_content = sub_content.strip().split("\n")[1:]
            if len(sub_content) == 0:
                continue
            individuals = _split_multiple_speakers(sub_content[1:])
            for individual in individuals:
                try:
                    subtitle = Subtitle(sub_content[0], individual, sterilize, offset, offset_is_negative)
                    if subtitle.has_content():
                        self.subtitles.append(subtitle)
                except ValueError as e:
                    sys.stderr.write(f'Value error in subtitle timestring "{sub_content[0]}": {e}\n')

        self.subtitles = self.merge_sentences()

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
