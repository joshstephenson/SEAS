#!/usr/bin/env python
"""
Looks for large gaps between subtitles to be used for splitting.
Uses one subtitle file as source to find the gaps and then splits into multiple files
and aligns target subtitle file with same gaps.
"""

import argparse
from src.helpers import get_text, collate_subs, find_in_range, find_partitions_equal_size, find_partitions_by_gap_size, \
    get_language_code_from_path
import regex
from datetime import datetime
from src.subtitle import Subtitle, SRT_TIME_FORMAT


def get_subtitles(contents, language, is_source) -> [Subtitle]:
    subtitles: [Subtitle] = []
    previous = None
    for sub_content in contents:
        if len(sub_content) == 0:
            continue
        current = Subtitle(sub_content, language = language)
        current.is_source = is_source
        # Reset the text because the Subtitle's init class wants to strip newlines
        current.text = "\n".join(contents[2:])
        # current = TimeCodes(start, end, previous)
        subtitles.append(current)
        if previous is not None:
            current.previous = previous
            previous.following = current
        previous = current
    return subtitles


def print_partitions(partitions, opts):
    source_idx = 1
    target_idx = 1
    for i, partition in enumerate(partitions):
        # Support for partitions up to 999
        infix = str(i + 1).rjust(3, '0')
        source_output = opts.source_file.replace('.srt', f'-{infix}.srt')
        target_output = opts.target_file.replace('.srt', f'-{infix}.srt')

        with open(source_output, 'w') as sf, open(target_output, 'w') as tf:
            # Write the source subs
            for sub in partition.source.subtitles:
                sf.write(sub.lines + '\n\n')
                source_idx += 1
            for sub in partition.target.subtitles:
                tf.write(sub.lines + '\n\n')
                target_idx += 1


def main(opts):
    source_text = get_text(opts.source_file)
    target_text = get_text(opts.target_file)

    source_contents = regex.split(r'\n{2,}', source_text)
    target_contents = regex.split(r'\n{2,}', target_text)

    source_lang = get_language_code_from_path(opts.source_file)
    target_lang = get_language_code_from_path(opts.target_file)

    source_subs = get_subtitles(source_contents, source_lang, True)
    target_subs = get_subtitles(target_contents, target_lang, False)

    collated = collate_subs(source_subs, target_subs)
    if opts.partition_count:
        partitions = find_partitions_equal_size(collated, opts.partition_count)
    else:
        partitions = find_partitions_by_gap_size(collated, opts.min_gap_length)
    print_partitions(partitions, opts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split pairs of subtitle files based on gaps between dialogue.")
    parser.add_argument('-s', '--source-file', required=True)
    parser.add_argument('-t', '--target-file', required=True)
    parser.add_argument('-g', '--min-gap-length', default=10, type=int, help='Minimum length of time between subtitles')
    parser.add_argument('-c', '--partition_count', type=int, required=False)
    parser.add_argument('-pg', '--print_gaps', default=False, action="store_true", help='just print out gaps')
    args = parser.parse_args()

    main(args)
