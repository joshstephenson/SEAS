import regex
import sys

from src.helpers import is_not_empty, collate_subs, find_partitions
from src.subtitle import Subtitle
from src.utterance_pair import UtterancePair
from src.utterance_options import UtteranceOptions
from src.utterance import Utterance


class Subtitles:
    """
    Subtitles is a class that takes in a body of text represent an SRT file and stores a list of subtitles associated
    with a single language. It also allows merging of sentences and aligning subtitles from another language based
    on timecodes.
    """

    def __init__(self, text, is_source=True):
        self.is_source = is_source
        # First strip bad carriage returns:
        text = regex.sub(r'\r', '', text).strip()

        self.index = 0
        self.subtitles = []

        # Split on 2 or more lines in a row
        sub_contents = regex.split(r'\n{2,}', text)

        previous_sub = None
        for sub_content in sub_contents:
            # Save the raw text in case we need to recreate it
            subtitle = None
            # try:
            subtitle = Subtitle(sub_content, is_source)
            # except ValueError as e:
            #     sys.stderr.write(f'Value error in subtitle timestring "{sub_content}": {e}\n')

            if subtitle is not None:
                self.subtitles.append(subtitle)
                if previous_sub is not None:
                    subtitle.previous = previous_sub
                    previous_sub.subsequent = subtitle
                previous_sub = subtitle

        self.utterances = self.find_utterances()

    def find_utterances(self):
        """
        Finds utterances across subtitles.
        Cases:
        1. One subtitle has more than one sentence.
        2. Two or more subtitles have one sentence spread across them.
        :return: list of unique utterances linked to their subtitles
        """
        utterances = [Utterance(text, [sub]) for sub in self.subtitles for text in sub.texts if is_not_empty(text)]
        to_delete = []
        previous = None
        for current in utterances:
            if current.ends_utterance():
                found_boundary = True
            else:
                found_boundary = False
                if previous is None:
                    previous = current
            if previous is not None and previous != current:
                if not current.starts_utterance():
                    previous.merge(current)
                    to_delete.append(current)
            if found_boundary:
                previous = None

        return [u for u in utterances if u not in to_delete]

    def find_utterances_for_sub(self, subtitle) -> list[Utterance]:
        return [u for u in self.utterances if subtitle in u.subtitles]

    def find_utterances_by_time(self, start, end) -> list[Utterance]:
        return [u for u in self.utterances if u.end() >= start and u.start() <= end]

    def align(self, target):
        # collated = collate_subs(self.subtitles, target.subtitles)
        # partitions = find_partitions(collated)
        # pairs = []
        # for partition in partitions:
        #     # print(partition)
        #     if len(partition.source.utterances) > 0 and len(partition.target.utterances) > 0:
        #         pairs.append([str(partition.source), str(partition.target)])
        # return pairs
        previous = None
        pairs = []
        for utterance in self.utterances:
            pair = UtterancePair(previous, utterance, target.find(utterance))
            pairs.append(pair)
            if previous is not None:
                previous.subsequent = pair
            previous = pair

        # Resolve overlaps
        resolved: list[UtterancePair] = []
        current = pairs[0]

        while current.subsequent is not None:
            current.resolve_multiple_targets()
            if not current.flagged_for_delete:
                resolved.append(current)
            current = current.subsequent
        resolved.append(current)

        for pair in resolved:
            pair.merge_options()

        return resolved

    def find(self, other: Utterance) -> UtteranceOptions:
        """
        Find the counterpart to a subtitle provided from another language in the current set
        :param other: a target utterance to find the match
        :return: counterpart subtitle or None
        """

        options = []
        for current in self.utterances:
            if current.end() < other.start():
                continue
            elif current.start() > other.end():
                break
            else:
                options.append(current)
        return UtteranceOptions(options)

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
