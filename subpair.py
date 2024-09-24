from subtitle import Subtitle
from suboptions import SubOptions


class SubPair:
    """
    SubPair is a class that has a one-to-many relationship between a source subtitle and target subtitles.
    This is due to the fact that subtitle timecodes often overlap between languages.
    This class is also used as a linked list to walk the subtitle pairs and resolve conflicts between them
    and their previous and subsequent subtitle pairs by moving, merging or altering subtitles.
    """
    def __init__(self, previous, source: Subtitle, sub_options: SubOptions):
        self.source = source
        self.sub_options = sub_options
        self.flagged_for_delete = False
        self.previous = previous
        self.subsequent = None

    def commonality_with(self, other):
        return self.sub_options.find_common(other.sub_options)

    def remove_option(self, option):
        self.sub_options.remove(option)

    def merge_options(self):
        self.sub_options.merge()

    def has_no_target(self):
        return len(self.sub_options) == 0

    def is_longer_than(self, limit=30) -> bool:
        if self.has_no_target():
            return False
        if len(str(self.source)) > limit and len(str(self.sub_options)) > limit:
            return True
        return False

    def target_sentences(self):
        sentences = self.sub_options.sentences()
        return [s for s in sentences if len(s)]

    def pop_last_sentence_as_subtitle(self) -> Subtitle:
        sentence = self.sub_options.remove_last_sentence()
        return sentence

    def add_option(self, option: Subtitle):
        self.sub_options.add_option(option)

    def append_sentence_to_source(self, sentence: str):
        self.source.text = self.source.text + ' ' + sentence

    def resolve_conflicts(self, sterilize=True, strip_captions=True):
        # Resolve situations where two subsequent source subtitles have overlap with the same target subtitle
        # by assigning the target sub to the source with the greatest overlap
        commonality = self.commonality_with(self.subsequent)
        if len(commonality) > 0:
            for opt in commonality:
                with_current = self.source.overlap(opt)
                with_subsequent = self.subsequent.source.overlap(opt)
                if with_current > with_subsequent:
                    self.subsequent.remove_option(opt)
                else:
                    self.remove_option(opt)

            # Sometimes a subtitle has no targets, most likely because the previous subtitle "swallowed" its target
            # So we should merge the sources
            if self.has_no_target():
                if self.previous is not None and len(self.previous.target_sentences()) > 1:
                    sub = self.previous.pop_last_sentence_as_subtitle()
                    if sub.has_content(sterilize, strip_captions):
                        self.add_option(sub)

            if self.subsequent.has_no_target:
                if len(self.target_sentences()) > 1:
                    sub = self.pop_last_sentence_as_subtitle()
                    if sub.has_content(sterilize, strip_captions):
                        self.subsequent.add_option(sub)

    def __str__(self):
        return f'{self.source}\n{self.sub_options}\n'