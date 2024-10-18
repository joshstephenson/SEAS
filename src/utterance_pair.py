from src.subtitle import Subtitle
from src.utterance import Utterance
from src.utterance_options import UtteranceOptions


class UtterancePair:
    """
    SubPair is a class that has a one-to-many relationship between a source subtitle and target subtitles.
    This is due to the fact that subtitle timecodes often overlap between languages.
    This class is also used as a linked list to walk the subtitle pairs and resolve conflicts between them
    and their previous and subsequent subtitle pairs by moving, merging or altering subtitles.
    """
    def __init__(self, previous, source: Utterance, options: UtteranceOptions):
        self.source = source
        self.options = options
        self.flagged_for_delete = False
        self.previous = previous
        self.subsequent = None

    def commonality_with(self, other):
        return self.options.find_common(other.options)

    def remove_option(self, option):
        if option in self.options.options:
            self.options.remove(option)

    def merge_options(self):
        self.options.merge()

    def has_no_target(self):
        return len(self.options) == 0

    def is_longer_than(self, limit=30) -> bool:
        if self.has_no_target():
            return False
        return len(str(self.source)) > limit and len(str(self.options)) > limit

    def target_utterances(self):
        return [s for s in self.options.options if len(s) > 0]

    def pop_last_sentence(self) -> Subtitle:
        return self.options.options.pop()

    def add_option(self, option: Subtitle):
        self.options.add_option(option)

    def append_sentence_to_source(self, sentence: str):
        self.source.text = self.source.text + ' ' + sentence

    def resolve_multiple_targets(self):
        # Resolve situations where two subsequent source subtitles have overlap with the same target utterance
        # by assigning the target utterance to the source with the greatest overlap
        commonality = self.commonality_with(self.subsequent)
        for target_opt in commonality:
            with_current = self.source.overlap(target_opt)
            with_subsequent = self.subsequent.source.overlap(target_opt)
            if with_current > with_subsequent:
                # print(f'removing {target_opt} from subsequent: {self.subsequent.source.text}')
                self.subsequent.remove_option(target_opt)
            else:
                # print(f'removing {target_opt} from current: {self.source.text}')
                self.remove_option(target_opt)

    def __str__(self):
        return f'{self.source}\n{self.options}\n'