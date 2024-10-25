#!/usr/bin/env python

import argparse
from src.helpers import get_text, get_language_code_from_path

from src.subtitles import Subtitles


def main(opts):
    # Read the files
    source_text = get_text(opts.source)
    target_text = get_text(opts.target)

    # Create Subtitle objects from the file texts
    source_subs = Subtitles(source_text, language=get_language_code_from_path(opts.source), is_source=True)
    target_subs = Subtitles(target_text, language=get_language_code_from_path(opts.source), is_source=False)

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
    parser.add_argument('--strict', default=2, type=int,
                        help='Don\'t print out subtitle pairs if they\'re shorter than certain length.')
    args = parser.parse_args()
    main(args)
