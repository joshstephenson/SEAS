import string

import numpy as np
import regex
import sys

from src.alignment import Alignment
from src.partition import Partition
from src.utterance import Utterance

MICROSECONDS_PER_SECOND = 1e6


def get_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as _:
        sys.stderr.write(f'UTF-8 decoding failed. Will try latin-1 encoding.' + '\n')
        with open(filename, 'r', encoding='latin-1') as source_file:
            srt_text = source_file.read()
    return srt_text


def get_ids_from_str(id_string):
    ids = regex.findall(r'\d+', id_string)
    return [int(i) for i in ids]


def get_alignments_from_file(paths_file, source_sent_file, target_sent_file, source_index_file, target_index_file):
    paths_file = open(paths_file, 'r', encoding='utf-8')
    source_file = open(source_sent_file, 'r', encoding='utf-8')
    source_idx_file = open(source_index_file, 'r', encoding='utf-8')
    target_file = open(target_sent_file, 'r', encoding='utf-8')
    target_idx_file = open(target_index_file, 'r', encoding='utf-8')

    paths = [a.strip() for a in paths_file.readlines()]
    # Using np arrays because they allow passing arrays as indices
    source_sentences = np.array([line.strip() for line in source_file.readlines()])
    target_sentences = np.array([line.strip() for line in target_file.readlines()])
    # Lookups for sentence index to subtitle index
    # one to many lookup with keys which correspond to lines in the .sent files
    # and values which are 1 or more subtitle indices.
    source_lookup = dict((i, np.array(get_ids_from_str(a))) for i, a in enumerate(source_idx_file.readlines()))
    target_lookup = dict((i, np.array(get_ids_from_str(a))) for i, a in enumerate(target_idx_file.readlines()))
    # for k, v in source_lookup.items():
    #     print(k, v)
    # exit(0)

    paths_file.close()
    source_file.close()
    source_idx_file.close()
    target_file.close()
    target_idx_file.close()

    alignments = []
    for path in paths:
        parts = path.split(':')
        source_idx = get_ids_from_str(parts[0])
        target_idx = get_ids_from_str(parts[1])
        # sound_idx and target_idx are arrays
        source_sentence = ' '.join(source_sentences[source_idx])
        target_sentence = ' '.join(target_sentences[target_idx])
        source_sub_idx = [source_lookup[idx] for idx in source_idx]
        target_sub_idx = [target_lookup[idx] for idx in target_idx]
        alignment = Alignment(source_sentence, target_sentence, source_sub_idx, target_sub_idx)
        alignments.append(alignment)

    return alignments


# def get_sentences_with_index(sent_file, index_file) -> [(str, str)]:
#     with open(sent_file, 'r', encoding='utf-8') as sent_file:
#         sent_lines = [i.strip() for i in sent_file.readlines()]
#     with open(index_file, 'r', encoding='utf-8') as index_file:
#         index_lines = [i.strip() for i in index_file.readlines()]
#     assert len(sent_lines) == len(index_lines)
#     return dict(zip(sent_lines, index_lines))


def microseconds_to_string(microseconds):
    milliseconds = int((microseconds / 1e3) % 1e3)
    seconds = int((microseconds / 1e6) % 60)
    minutes = int((microseconds / (1e6 * 60)) % 60)
    hours = int((microseconds / (1e6 * 60 * 60)) % 24)

    hours = str(hours).rjust(2, '0')
    minutes = str(minutes).rjust(2, '0')
    seconds = str(seconds).rjust(2, '0')
    milliseconds = str(milliseconds).rjust(3, '0')
    return f'{hours}:{minutes}:{seconds},{milliseconds}'


def collate_subs(first, second):
    """
    Returns collated and sorted list of subtitles from both first and second
    """
    return sorted(first + second, key=lambda sub: sub.start)


# def find_utterances(self):
#     """
    # Finds utterances across subtitles.
    # Cases:
    # 1. One subtitle has more than one sentence.
    # 2. Two or more subtitles have one sentence spread across them.
    # :return: list of unique utterances linked to their subtitles
    # """
    # utterances = [Utterance(text, [sub]) for sub in self.subtitles for text in sub.texts]
    # to_delete = []
    # current = None
    # for utterance in utterances:
    #     if regex.search(SENT_BOUNDARIES_REGEX, utterance.text):
    #         found_boundary = True
    #     else:
    #         found_boundary = False
    #         if current is None:
    #             current = utterance
    #     if current is not None and current != utterance:
    #         current.merge(utterance)
    #         to_delete.append(utterance)
    #     if found_boundary:
    #         current = None
    #
    # return [u for u in utterances if u not in to_delete]


def find_in_range(subtitles, start, end):
    """
    Find all subtitles in a given time range and return them in a list
    Does not necessarily return subtitles linked
    """
    return [subtitle for subtitle in subtitles if subtitle.end > start and subtitle.start < end]


def find_all(subtitles, start, end):
    """
    Find all subtitles and subtitles they're linked to in a given time range and return them in a list
    """
    stack = find_in_range(subtitles, start, end)
    searched = []
    found = set()
    while len(stack) > 0:
        subtitle = stack.pop()
        searched.append(subtitle)
        found.add(subtitle)
        for subtitle in find_in_range(subtitles, subtitle.start, subtitle.end):
            if subtitle not in searched:
                stack.append(subtitle)
        for adj in subtitle.linked_via_utterance():
            if adj not in searched:
                stack.append(adj)
    return found


# def partition(source_subs, target_subs, opts):
#     collated = collate_subs(source_subs, target_subs)
#     sections = find_partitions(collated, opts.min_gap_length * MICROSECONDS_PER_SECOND, opts.print_gaps)
#
#     return [find_all(collated, section['start'], section['end']) for section in sections]


def find_partitions(collated) -> [Partition]:
    """
    :param collated: a list of subtitles in source and target langs sorted by subtitle.start
    :returns: a list of partitions
    """
    partitions = []
    index = 0
    current_partition = None

    while len(collated) > 0:
        current_partition = Partition(index)
        index += 1
        partitions.append(current_partition)
        subtitle = collated[0]
        current_partition.append(subtitle)
        for related in find_all(collated, subtitle.start, subtitle.end):
            if related in collated:
                collated.remove(related)
            current_partition.append(related)

    return partitions


def print_partition(partition):
    print("SOURCE: ", len(partition.source.subtitles), len(partition.source.utterances))
    for sub in partition.source.subtitles:
        print(sub)
        print("-----")
    for utterance in partition.source.utterances:
        print(utterance, "\n")

    print("TARGET ", len(partition.target.subtitles), len(partition.target.utterances))
    for sub in partition.target.subtitles:
        print(sub, "\n")
        print("-----")
    for utterance in partition.target.utterances:
        print(utterance, "\n")
    print("")


def find_partitions_by_gap_size(collated, gap_length, print_gaps=False):
    """
    Find sections between gaps of certain size
    """
    sections = []
    gaps = []
    last_gap = 0
    last_start = 0
    previous = None
    for subtitle in collated:
        if previous is not None:
            last_gap = subtitle.start - previous.end
        if last_gap >= gap_length:
            gaps.append(last_gap)
            # Get the length of the time between gaps, not the length of the gap
            length = previous.end - last_start
            sections.append({'length': length, 'start': last_start, 'end': previous.end, 'gap': last_gap})
            last_start = subtitle.start
        previous = subtitle

    if print_gaps and len(sections):
        for gap in sorted(gaps):
            print(microseconds_to_string(gap))
    #     for section in sections:
    #         start = microseconds_to_string(section['start'])
    #         end = microseconds_to_string(section['end'])
    #         length = microseconds_to_string(section['length'])
    #         last_gap = microseconds_to_string(section['gap'])
    #         print(f'-----------------\n     {start}\n     {end}\n-----------------\nGAP: {last_gap}')

    return sections


def is_not_empty(text):
    """
    Returns true if text has characters other than punctuation
    """
    text = text.translate(str.maketrans('', '', string.punctuation)).strip()
    return len(text) > 0
