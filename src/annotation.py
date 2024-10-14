from difflib import SequenceMatcher


class Annotation:
    class Language:
        def __init__(self, subtitles, utterance, is_source=True):
            self.is_source = is_source
            self.subtitles = subtitles
            self.utterance = utterance

        def lines(self) -> str:
                return "\n\n".join(s.lines for s in self.subtitles)

        def get_offsets_and_length(self, subtitle):
            """
            returns y,x and length for curses highlighting
            """
            text = subtitle.lines
            content_lines = '\n'.join(text.split("\n")[:2])
            if text.count('\n') > 2:
                match = SequenceMatcher(None, self.utterance, text.replace('\n', ' ')).find_longest_match()
            else:
                match = SequenceMatcher(None, self.utterance, text).find_longest_match()
            y_offset = 0
            length = match.size

            x_orig = max(match.a, match.b)
            x_offset = x_orig
            for line in text.split('\n')[:-1]:
                if x_offset - len(line) > 0:
                    x_offset -= len(line) + 1
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
