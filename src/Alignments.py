from src.helpers import get_alignments_from_file


class Alignments:
    def __init__(self, path_file, source_sent_file, source_index_file, target_sent_file, target_index_file):
        self.alignments = get_alignments_from_file(path_file,
                                                   source_sent_file,
                                                   target_sent_file,
                                                   source_index_file,
                                                   target_index_file)
        # print([str(s) for s in self.alignments])

