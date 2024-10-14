#!/usr/bin/env python
"""
Looks for large gaps between subtitles to be used for splitting.
Uses one subtitle file as source to find the gaps and then splits into multiple files
and aligns target subtitle file with same gaps.
"""

import argparse
from src.helpers import get_text, SRT_TIME_FORMAT
import regex
from datetime import datetime

# def get_subtitles(contents, offset, is_source) -> [Subtitle]:
#     subtitles: [Subtitle] = []
#     previous = None
#     for sub_content in contents:
#         if len(sub_content) == 0:
#             continue
#         # timecodes are on the 2nd line
#         contents = sub_content.strip().split("\n")
#         timecode_string = contents[1]
#         current = Subtitle(timecode_string, contents[2:])
#         current.is_source = is_source
#         # Reset the text because the Subtitle's init class wants to strip newlines
#         current.text = "\n".join(contents[2:])
#         # current = TimeCodes(start, end, previous)
#         subtitles.append(current)
#         if previous is not None:
#             current.previous = previous
#             previous.following = current
#         previous = current
#     return subtitles


def print_partitions(partitions, opts):
    source_idx = 1
    target_idx = 1
    for i, s in enumerate(partitions):
        # Support for partitions up to 999
        infix = str(i + 1).rjust(3, '0')
        source_output = opts.source_file.replace('.srt', f'-{infix}.srt')
        target_output = opts.target_file.replace('.srt', f'-{infix}.srt')

        with open(source_output, 'w') as sf, open(target_output, 'w') as tf:
            # Write the source subs
            for j, sub in enumerate(s):
                if sub.is_source:
                    sf.write(str(source_idx) + '\n')
                    sf.write(sub.timestring + '\n')
                    sf.write(sub.text + '\n\n')
                    source_idx += 1
                else:
                    tf.write(str(target_idx) + '\n')
                    tf.write(sub.timestring + '\n')
                    tf.write(sub.text + '\n\n')
                    target_idx += 1


def main(opts):
    source_text = get_text(opts.source_file)
    target_text = get_text(opts.target_file)

    offset = datetime.strptime('00:00:00,000', SRT_TIME_FORMAT)
    source_contents = regex.split(r'\n{2,}', source_text)
    target_contents = regex.split(r'\n{2,}', target_text)

    source_subs = get_subtitles(source_contents, offset, True)
    target_subs = get_subtitles(target_contents, offset, False)

    partitions = partition(source_subs, target_subs, opts)
    print_partitions(partitions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split pairs of subtitle files based on gaps between dialogue.")
    parser.add_argument('-s', '--source-file', required=True)
    parser.add_argument('-t', '--target-file', required=True)
    parser.add_argument('-g', '--min-gap-length', default=10, type=int, help='Minimum length of time between subtitles')
    parser.add_argument('-pg', '--print_gaps', default=False, action="store_true", help='just print out gaps')
    args = parser.parse_args()

    main(args)
