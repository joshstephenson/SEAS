#!/usr/bin/env python

import argparse
import os
from src.helpers import get_text

# local imports
from src.subtitles import Subtitles

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
    source_subs = Subtitles(source_text, is_source=True)
    target_subs = Subtitles(target_text, is_source=False)

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
    parser.add_argument('--strict', default=2, type=int, help='Don\'t print out subtitle pairs if they\'re shorter than certain length.')
    args = parser.parse_args()
    main(args)
