#!/usr/bin/env python
"""
Extract sentences from SRT file after preprocessing. Writes to STDOUT.
"""
import argparse
import os
import sys
import regex

from src.config import Config
from src.helpers import get_text, find_partitions, collate_subs, find_partitions_by_gap_size, merge_ellipsized
from src.subtitle import sterilize
from src.subtitles import Subtitles


def layer(lines, num_overlaps, comb=' '):
    out = []
    for ii in range(len(lines) - num_overlaps + 1):
        out.append(comb.join(lines[ii:ii + num_overlaps]))
    return out


def yield_overlaps(lines, num_overlaps):
    for overlap in range(1, num_overlaps + 1):
        for out_line in layer(lines, overlap):
            yield out_line


def close_files(files):
    for file in files:
        file.close()


def open_associated_files(srt_filename) -> (str, str, str):
    return (open(srt_filename.replace('.srt', '.sent'), 'w', encoding='utf-8'),
            open(srt_filename.replace('.srt', '.sent-index'), 'w', encoding='utf-8'),
            open(srt_filename.replace('.srt', '.overlap'), 'w', encoding='utf-8'))


def main(opts):
    sys.stderr.write(f'Overlap size: {opts.num_overlaps}, Gap length: {opts.gap_length}' + '\n')
    source_text = get_text(opts.source)
    target_text = get_text(opts.target)

    source_subs = Subtitles(source_text, is_source=True)
    target_subs = Subtitles(target_text, is_source=False)

    source_sent_file, source_index_file, source_overlap_file = open_associated_files(opts.source)
    target_sent_file, target_index_file, target_overlap_file = open_associated_files(opts.target)

    collated = collate_subs(source_subs.subtitles, target_subs.subtitles)
    partitions = find_partitions_by_gap_size(collated, opts.gap_length)
    partitions = merge_ellipsized(partitions)

    source_overlaps = set()
    target_overlaps = set()

    for partition in partitions:
        for utterance in partition.source.utterances:
            source_sent_file.write(utterance.text + '\n')
            if opts.index:
                source_index_file.write(str(sorted([sub.index for sub in utterance.subtitles])) + '\n')

        for utterance in partition.target.utterances:
            target_sent_file.write(utterance.text + '\n')
            if opts.index:
                target_index_file.write(str(sorted([sub.index for sub in utterance.subtitles])) + '\n')

        for line in yield_overlaps([u.text for u in partition.source.utterances], opts.num_overlaps):
            source_overlaps.add(line)

        for line in yield_overlaps([u.text for u in partition.target.utterances], opts.num_overlaps):
            target_overlaps.add(line)

    source_overlaps = list(source_overlaps)
    source_overlaps.sort()
    for line in source_overlaps:
        source_overlap_file.write(line + '\n')

    target_overlaps = list(target_overlaps)
    target_overlaps.sort()
    for line in target_overlaps:
        target_overlap_file.write(line + '\n')

    close_files([source_sent_file, source_index_file, source_overlap_file,
                 target_sent_file, target_index_file, target_overlap_file])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True)
    parser.add_argument('-t', '--target', required=True)
    parser.add_argument('-n', '--num-overlaps', type=int, default=Config.NumOverlaps)
    parser.add_argument('-g', '--gap-length', type=float, default=Config.GapThreshold,
                        help='Gap length in seconds. Will partition subtitles based on this gap length.')
    parser.add_argument('-i', '--index', action="store_true",
                        help="Include a file that prints the indices associated with each sentence.")
    args = parser.parse_args()

    main(args)
