from nltk import sent_tokenize
from subtitle import Subtitle


class SubOptions:
    """
    SubOptions is a class that acts as a wrapper for a list of subtitles.
    It facilitates finding overlap with other lists of subtitles and merging those subtitles when necessary.
    """
    def __init__(self, options: [Subtitle]):
        self.options = options
        self.index = 0

    def find_common(self, other):
        """
        Find target subtitles that are common between this object and other
        :return: list of target subtitles (typically just one)
        """
        common = []
        for opt in self.options:
            if opt in other.options:
                common.append(opt)
        return common

    def merge(self):
        """
        Merge all target subtitles (target options) into one
        """
        if len(self.options) == 0:
            return

        merged = []
        first = self.options[0]
        merged.append(first)
        for other in self.options[1:]:
            first.merge(other)
        self.options = merged

    def remove(self, item):
        self.options.remove(item)

    def sentences(self) -> [str]:
        text = " ".join(str(s) for s in self.options)
        sentences = sent_tokenize(text)
        return sentences

    def remove_last_sentence(self) -> Subtitle:
        opt: Subtitle = self.options[-1]
        sentence = self.sentences()[-1]
        opt.text = opt.text.replace(sentence, '')
        sub = Subtitle(opt.timestring, sentence, opt.sterilized, opt.offset, opt.offset_is_negative)
        return sub

    def add_option(self, option: Subtitle):
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
