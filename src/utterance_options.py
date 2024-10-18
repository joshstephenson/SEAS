from nltk import sent_tokenize
from src.subtitle import Subtitle
from src.utterance import Utterance


class UtteranceOptions:
    """
    SubOptions is a class that acts as a wrapper for a list of subtitles.
    It facilitates finding overlap with other lists of subtitles and merging those subtitles when necessary.
    """
    def __init__(self, options: [Utterance]):
        self.options = options
        self.index = 0

    def find_common(self, other):
        return [opt for opt in self.options if opt in other.options]

    def merge(self):
        """
        Merge all target utterances (target options) into one
        """
        if len(self.options) == 0:
            return

        first = self.options[0]
        while len(self.options) > 1:
            other = self.options.pop(1)
            first.merge(other)

    def remove(self, item: Utterance):
        self.options.remove(item)

    def add_option(self, option: Utterance):
        self.options.append(option)

    def __len__(self):
        return len(self.options)

    def __str__(self):
        return "--".join(str(s) for s in self.options).strip()

    def __iter__(self):
        self.index = -1
        self.current = self.options[self.index]
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.options):
            self.current = self.options[self.index]
            return self.current
        else:
            raise StopIteration
