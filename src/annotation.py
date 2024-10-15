from difflib import SequenceMatcher


class Annotation:
    class Language:
        def __init__(self, subtitles, utterance, is_source=True):
            self.is_source = is_source
            self.subtitles = subtitles
            self.utterance = utterance

        def lines(self) -> str:
            return "\n\n".join(s.lines for s in self.subtitles)

        def get_offsets_and_length(self, line):
            """
            returns y,x and length for curses highlighting
            """
            match = SequenceMatcher(None, self.utterance, line).find_longest_match()
            y_offset = 0
            length = match.size
            x_offset = match.b # max(match.a, match.b)
            y_offset += 1

            return y_offset, x_offset, length

        def has_subtitles(self) -> bool:
            return len(self.subtitles) > 0

        def has_utterance(self) -> bool:
            return self.utterance is not None

    def __init__(self, source_subs, target_subs, source_utterance, target_utterance):
        self.source = Annotation.Language(source_subs, source_utterance, is_source=True)
        self.target = Annotation.Language(target_subs, target_utterance, is_source=False)


    def order(self) -> int:
        print([sub.index for sub in self.source.subtitles])
        return min([sub.index for sub in self.source.subtitles])

    def is_stranded(self) -> bool:
        return self.source.utterance is None and self.target.utterance is None
