#!/usr/bin/env python

import argparse
import os
from helpers import get_text

# local imports
from subtitles import Subtitles

def main(opts):
    # find the full path of the file arguments
    source = os.path.expanduser(opts.source)
    target = os.path.expanduser(opts.target)

    # Check that these files exist
    if not os.path.exists(source):
        raise (Exception(f"source path does not exist: {source}"))
    if not os.path.exists(target):
        raise (Exception(f"target path does not exist: {target}"))

    # Read the files
    source_text = get_text(source)
    target_text = get_text(target)

    # Create Subtitle objects from the file texts
    source_subs = Subtitles(source_text)
    target_subs = Subtitles(target_text, opts.offset, opts.offset_is_negative)

    # Now align the subtitles based on timecodes
    pairs = source_subs.align(target_subs)

    # Output the aligned sentences
    for pair in pairs:
        if pair.is_longer_than(opts.strict):
            print(pair)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True)
    parser.add_argument('-t', '--target', required=True)
    parser.add_argument('-o', '--offset', required=False, default='00:00:00,000', type=str,
                        help='Time offset between source and target in SRT format. .e.g 00:00:12,500.')
    parser.add_argument('--offset-is-negative', default=False, action='store_true',
                        help='Indicates that the target is ahead of the source.')
    parser.add_argument('--strict', default=12, type=int, help='Don\'t print out subtitle pairs if they\'re shorter than certain length.')
    args = parser.parse_args()
    main(args)
