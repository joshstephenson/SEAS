from src.Alignments import Alignments
from src.annotation import Annotation
from src.helpers import get_text
from src.subtitles import Subtitles


class Film:
    class Language:
        def __init__(self, srt_file, is_source=True):
            self.is_source = is_source
            self.label = srt_file.split('/')[-1].split('.')[0]
            text = get_text(srt_file)
            self.subtitles = Subtitles(text, is_source).subtitles

    def __init__(self, source_file, target_file, alignments: Alignments):
        self.source = Film.Language(source_file, is_source=True)
        self.target = Film.Language(target_file, is_source=False)
        self.alignments = alignments
        stranded_subs = [sub.index for sub in self.source.subtitles]
        self.annotations = []
        for alignment in self.alignments.alignments:
            alignment.source_subs = [sub for sub in self.source.subtitles if sub.index in alignment.source_ids]
            alignment.target_subs = [sub for sub in self.target.subtitles if sub.index in alignment.target_ids]
            self.annotations.append(Annotation(alignment.source_subs,
                                               alignment.target_subs,
                                               alignment.source,
                                               alignment.target))
            for sub in alignment.source_subs:
                if sub.index in stranded_subs:
                    stranded_subs.remove(sub.index)
        for sub in self.source.subtitles:
            assert sub.index > 0
            if sub.index in stranded_subs:
                if sub is not None and sub.index > 0:
                    self.annotations.append(Annotation([sub],
                                                       [],
                                                       None,
                                                       None))
        self.annotations = [annot for annot in self.annotations if len(annot.source.subtitles) > 0]
        self.annotations = sorted(self.annotations, key=lambda annot: annot.order())
        self.annotation_index = 0

    def total(self) -> int:
        return len(self.annotations)

    def previous(self):
        self.annotation_index -= 1

    def next(self):
        self.annotation_index += 1

    def get_annotation(self) -> Annotation:
        return self.annotations[self.annotation_index]
