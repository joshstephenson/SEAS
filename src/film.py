import sys

from src.alignments import Alignments
from src.annotation import Annotation
from src.helpers import get_text
from src.subtitles import Subtitles
import copy


class Film:
    class Language:
        def __init__(self, srt_file, is_source=True):
            self.is_source = is_source
            self.label = srt_file.split('/')[-1].split('.')[0]
            self.language_code = srt_file.split('/')[-2]
            text = get_text(srt_file)
            self.subtitles = Subtitles(text, self.language_code, is_source).subtitles

    def __init__(self, source_file, target_file, alignments: Alignments, ignore_stranded=False):
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
        if not ignore_stranded:
            for sub in self.source.subtitles:
                if sub.index in stranded_subs:
                    if sub is not None and sub.index > 0:
                        self.annotations.append(Annotation([sub],
                                                           [],
                                                           None,
                                                           None))
        self.annotations = [annot for annot in self.annotations if len(annot.source.subtitles) > 0]
        self.annotations = sorted(self.annotations, key=lambda annot: annot.order())
        self.annotation_index = 0
        self.stranded_count = len(stranded_subs)
        self.total = len(self.annotations)
        self.added = 0

    def previous(self):
        self.annotation_index = max(0, self.annotation_index - 1)

    def next(self):
        if self.annotation_index < len(self.annotations) - 1:
            self.annotation_index += 1

    def get_annotation(self) -> Annotation:
        return self.annotations[self.annotation_index]

    def clear_annotation(self, annotation: Annotation):
        annotation.target.subtitles = []
        annotation.target.utterance = None
        annotation.source.utterance = None
        self.stranded_count += 1

    def split_annotation(self) -> None:
        annotation = self.get_annotation()
        self.added += 1
        duplicate = Annotation(annotation.source.subtitles,
                               annotation.target.subtitles,
                               annotation.source.utterance,
                               annotation.target.utterance)
        self.annotations.insert(self.annotation_index, duplicate)
        self.total = len(self.annotations)

    def join_annotation_with_subsequent(self) -> Annotation:
        annotation = self.get_annotation()
        next_annotation = self.annotations[self.annotation_index + 1]
        offset = 1
        while next_annotation.target.utterance is None:
            next_annotation = self.annotations[self.annotation_index + offset]
            offset += 1
        annotation.source.utterance += ' ' + next_annotation.source.utterance
        annotation.target.utterance += ' ' + next_annotation.target.utterance
        annotation.source.subtitles.extend(next_annotation.source.subtitles)
        annotation.target.subtitles.extend(next_annotation.target.subtitles)
        self.annotations.remove(next_annotation)
        self.total = len(self.annotations)

    def calculated_offset(self) -> float:
        """
        Will return offset in microseconds between source and subs.
        - If negative, it means the source subtitles are ahead of the target.
        - If positive, it means the target subtitles are behind the target.
        Uses 20 alignments in the middle, takes an average of the offsets
        """
        # Check 20 alignments in the middle
        total = len(self.alignments.alignments)
        if total < 40:
            sys.stderr.write(f'Not enough alignments to check for issues for {total}.')
            exit(1)
        start = (total // 2) - 10
        offsets = []
        count = 0
        for alignment in self.alignments.alignments[start:start+20]:
            source_subs = [sub.start for sub in alignment.source_subs]
            target_subs = [sub.start for sub in alignment.target_subs]
            if len(source_subs) == 0 or len(target_subs) == 0:
                continue
            source_min = min(source_subs)
            source_max = max(source_subs)
            target_min = min(target_subs)
            target_max = max(target_subs)
            start_diff = abs(target_min - source_min)
            end_diff = abs(target_max - source_max)
            offset = (start_diff + end_diff) / 2.0
            offsets.append(offset)
            count += 1

        return sum(offsets) / count

