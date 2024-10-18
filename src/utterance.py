from regex import regex

from src.subtitle import Subtitle

ENDS_UTTERANCE_REGEX = r'[\!\.\?]$'
STARTS_UTTERANCE_REGEX = r'^[A-Z¿¡-]'


class Utterance:
    """
    Associates a single utterance with one or more subtitles
    """
    def __init__(self, text, subtitles: [Subtitle]):
        self.text = text
        self.subtitles = set(subtitles)
        for subtitle in self.subtitles:
            subtitle.utterances.add(self)

    def __str__(self):
        return self.text

    def __len__(self):
        return len(self.text)

    def has_content(self) -> bool:
        return len(self.text) > 0

    def append(self, subtitle: Subtitle):
        self.subtitles.add(subtitle)
        subtitle.utterances.add(self)

    def overlap(self, other: "Utterance"):
        """
        Find the duration of time two subtitles overlap with each other
        :param other: the other subtitle to compare with self
        :return: duration of time two subtitles overlap with each other
        """
        start = max(self.start(), other.start())
        end = min(self.end(), other.end())
        return end - start

    def merge(self, other):
        """
        Merge another utterance with this one. Used when an utterance is spread across multiple subtitles.
        :param other: other subtitle to merge
        """
        self.text = " ".join([self.text, other.text]).replace('...', '').strip()
        for subtitle in other.subtitles:
            subtitle.utterances = set([self])
        for subtitle in self.subtitles:
            subtitle.utterances.add(self)
        self.subtitles.update(other.subtitles)

    def start(self) -> int:
        return min(sub.start for sub in self.subtitles)

    def end(self) -> int:
        return max(sub.end for sub in self.subtitles)

    def ends_utterance(self) -> bool:
        return regex.search(ENDS_UTTERANCE_REGEX, self.text.strip()) is not None

    def starts_utterance(self) -> bool:
        return regex.search(STARTS_UTTERANCE_REGEX, self.text.strip()) is not None
