import copy
import os
import string

import numpy as np
import regex
import sys

from src.alignment import Alignment
from src.partition import Partition
from src.utterance import Utterance

MICROSECONDS_PER_SECOND = 1e6


def get_text(filename):
    file = os.path.expanduser(filename)
    if not os.path.exists(file):
        raise (Exception(f"File path does not exist: {file}"))
    try:
        with open(filename, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as _:
        sys.stderr.write(f'UTF-8 decoding failed. Using Latin-1.' + '\n')
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


def find_utterances(subtitles):
    """
    Finds utterances across subtitles.
    Cases:
    1. One subtitle has more than one sentence.
    2. Two or more subtitles have one sentence spread across them.
    :return: list of unique utterances linked to their subtitles
    """
    utterances = [Utterance(text, [sub]) for sub in subtitles for text in sub.texts if is_not_empty(text)]
    if len(utterances) == 0:
        return []

    merged = []
    queue = copy.copy(utterances)
    current = queue.pop(0)
    while queue:
        if current.ends_utterance() or queue[0].starts_utterance():
            merged.append(current)
            current = queue.pop(0)
        else:
            current.merge(queue.pop(0))

    # Append the last current utterance
    merged.append(current)

    return merged


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


def find_partitions_by_gap_size(collated, gap_length):
    """
    Partition collated subtitles between gaps of certain length
    """
    sections = []
    gaps = []
    last_gap = 0
    last_start = 0
    previous = None
    # First find the gaps
    for subtitle in collated:
        if previous is not None:
            last_gap = subtitle.start - previous.end
        if last_gap >= gap_length * 1e6:
            gaps.append(last_gap)
            # Get the length of the time between gaps, not the length of the gap
            length = previous.end - last_start
            sections.append({'length': length, 'start': last_start, 'end': previous.end, 'gap': last_gap})
            last_start = subtitle.start
        previous = subtitle

    # Now use the time ranges to gather the subtitles
    partitions = []
    index = 0
    for section in sections:
        partition = Partition(index)
        index += 1
        for sub in find_in_range(collated, section['start'], section['end']):
            sub.utterances = set()  # clear utterances generated by Subtitles class
            partition.append(sub)
        partitions.append(partition)
        partition.source.utterances += find_utterances(partition.source.subtitles)
        partition.target.utterances += find_utterances(partition.target.subtitles)
    return partitions


FIVE_SECONDS = 10 * 1e6


def merge_ellipsized(partitions: [Partition], threshold_seconds) -> [Partition]:
    queue = copy.copy(partitions)
    merged = []
    current = queue.pop(0)
    while queue:
        if (current.gap_between(queue[0]) < (threshold_seconds * 1e6) and
                ((current.source.has_utterances() and current.source.utterances[-1].trails_off())
                 or (current.target.has_utterances() and current.target.utterances[-1].trails_off()))):
            current.merge(queue.pop(0))
        else:
            merged.append(current)
            current = queue.pop(0)

    # Append the last current utterance
    merged.append(current)

    return merged


def find_partitions_equal_size(subtitles, n, gap_threshold=5 * 1e6):
    total_subtitles = len(subtitles)
    base_size = total_subtitles // n
    remainder = total_subtitles % n

    partitions = []
    current_partition = []
    start_idx = 0

    for i in range(n):
        # Calculate how many subtitles to include in this partition
        partition_size = base_size + (1 if i < remainder else 0)

        # Start building the partition
        current_partition = subtitles[start_idx:start_idx + partition_size]

        # Check if there's enough gap after this partition
        if i < n - 1:  # No need to check for the last partition
            end_of_current_partition = current_partition[-1].end
            start_of_next_partition = subtitles[start_idx + partition_size].start

            gap = start_of_next_partition - end_of_current_partition

            # If the gap is too small, extend the partition
            while gap < gap_threshold and start_idx + partition_size < total_subtitles - 1:
                partition_size += 1
                current_partition = subtitles[start_idx:start_idx + partition_size]
                end_of_current_partition = current_partition[-1].end
                start_of_next_partition = subtitles[start_idx + partition_size].start
                gap = start_of_next_partition - end_of_current_partition

        partitions.append(current_partition)
        start_idx += partition_size

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


def is_not_empty(text):
    """
    Returns true if text has characters other than punctuation
    """
    text = text.translate(str.maketrans('', '', string.punctuation)).strip()
    return len(text) > 0
