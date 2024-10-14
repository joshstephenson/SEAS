from src.subtitle import Subtitle


class Partition:
    class Language:
        """
        Side is either source or target
        """

        def __init__(self, is_source=True):
            self.is_source = is_source
            self.subtitles = []
            self.utterances = []

        def add_subtitle(self, subtitle: Subtitle):
            if subtitle not in self.subtitles:
                self.subtitles.append(subtitle)
                for utterance in subtitle.utterances:
                    if utterance not in self.utterances:
                        self.utterances.append(utterance)
            self.subtitles = sorted(self.subtitles, key=lambda sub: sub.start)
            start = min(s.start for s in self.subtitles)
            end = max(s.end for s in self.subtitles)
            return start, end

    def __init__(self, index):
        self.index = index
        self.source = Partition.Language(True)
        self.target = Partition.Language(False)
        self.start = 0
        self.end = 0

    def append(self, subtitle):
        if subtitle.is_source:
            self.start, self.end = self.source.add_subtitle(subtitle)
        else:
            self.start, self.end = self.target.add_subtitle(subtitle)

    def merge_utterances(self) -> None:
        """
        If source language subtitles have one utterance whose target subtitles have two for the same translation,
        Merge the target ones. Vice versa applies as well.
        """

        def _do_merge(retain, remaining):
            for u in remaining:
                retain.text += ' FOO ' + u.text
                for sub in u.subtitles:
                    sub.utterances.remove(u)
                    if retain not in sub.utterances:
                        sub.utterances.append(retain)
                remaining.remove(u)

        if len(self.source.utterances) > len(self.target.utterances):
            if len(self.target.utterances) == 1:
                utterance = self.source.utterances[0]
                _do_merge(utterance, self.source.utterances[1:])
        else:
            if len(self.source.utterances) == 1:
                utterance = self.target.utterances[0]
                _do_merge(utterance, self.target.utterances[1:])

    def should_include(self, subtitle):
        """
        Only returns true if the subtitle should belong to this partition but doesn't already
        """
        return (subtitle not in self.source.subtitles and
                subtitle not in self.target.subtitles and
                subtitle.end > self.start or subtitle.start < self.end)

    def __str__(self):
        return f'Subs: {len(self.source.subtitles)} <-> {len(self.target.subtitles)}, ' +\
            f'Utterances: {len(self.source.utterances)} <-> {len(self.target.utterances)}'

    def __len__(self):
        return len(self.source.subtitles) + len(self.target.subtitles)
