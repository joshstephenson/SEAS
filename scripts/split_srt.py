#!/usr/bin/env python
"""
Looks for large gaps between subtitles to be used for splitting.
Uses one subtitle file as source to find the gaps and then splits into multiple files
and aligns target subtitle file with same gaps.
"""

import argparse
from helpers import get_text, SRT_TIME_FORMAT
import regex
from datetime import datetime
from subtitle import Subtitle


def find_all(subtitles, start, end):
    """
    Find all subtitles in a given time range and return them in a list
    """
    return [subtitle for subtitle in subtitles if subtitle.end > start and subtitle.start < end]

def get_subtitles(contents, offset) -> [Subtitle]:
    subtitles: [Subtitle] = []
    previous = None
    for sub_content in contents:
        if len(sub_content) == 0:
            continue
        # timecodes are on the 2nd line
        contents = sub_content.strip().split("\n")
        timecode_string = contents[1]
        current = Subtitle(timecode_string, contents[2:], offset)
        # Reset the text because the Subtitle's init class wants to strip newlines
        current.text = "\n".join(contents[2:])
        # current = TimeCodes(start, end, previous)
        subtitles.append(current)
        if previous is not None:
            current.previous = previous
            previous.following = current
        previous = current
    return subtitles

def main(opts):
    source_text = get_text(opts.source_file)
    target_text = get_text(opts.target_file)

    offset = datetime.strptime('00:00:00,000', SRT_TIME_FORMAT)
    source_contents = regex.split(r'\n{2,}', source_text)
    target_contents = regex.split(r'\n{2,}', target_text)

    source_subs = get_subtitles(source_contents, offset)
    target_subs = get_subtitles(target_contents, offset)

    sections = []
    last_gap = 0
    last_start = 0
    for subtitle in source_subs:
        if subtitle.previous is not None:
            last_gap = subtitle.start - subtitle.previous.end
        if last_gap >= (opts.min_gap_length * 1e6):
            length = subtitle.previous.end - last_start
            sections.append({'length': length, 'start': last_start, 'end': subtitle.previous.end})
            last_start = subtitle.start

    source_groups = []
    target_groups = []
    for section in sections:
        source_groups.append(find_all(source_subs, section['start'], section['end']))
        target_groups.append(find_all(target_subs, section['start'], section['end']))

    for i, (s, t) in enumerate(zip(source_groups, target_groups)):
        infix = str(i + 1).rjust(3, '0')
        source_output = opts.source_file.replace('.srt', f'-{infix}.srt')
        target_output = opts.target_file.replace('.srt', f'-{infix}.srt')

        with open(source_output, 'w') as sf, open(target_output, 'w') as tf:
            # Write the source subs
            for j, sub in enumerate(s):
                sf.write(str(j+1) + '\n')
                sf.write(sub.timestring + '\n')
                sf.write(sub.text + '\n\n')

            # Write the target subs
            for j, sub in enumerate(t):
                tf.write(str(j+1) + '\n')
                tf.write(sub.timestring + '\n')
                tf.write(sub.text + '\n\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split pairs of subtitle files based on gaps between dialogue.")
    parser.add_argument('-s', '--source-file', required=True)
    parser.add_argument('-t', '--target-file', required=True)
    parser.add_argument('-g', '--min-gap-length', default=10, type=int, help='Minimum length of time between subtitles')
    args = parser.parse_args()

    main(args)
