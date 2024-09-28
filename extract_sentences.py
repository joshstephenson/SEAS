#!/usr/bin/env python
import argparse
import os
import sys

from subtitles import Subtitles

def get_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as e:
        print(f'UTF-8 decoding failed. Will try latin-1 encoding.')
        with open(filename, 'r', encoding='latin-1') as source_file:
            srt_text = source_file.read()
    return srt_text


def main(opts):
    file = os.path.expanduser(opts.file)
    if not os.path.exists(file):
        raise (Exception(f"File path does not exist: {file}"))
    text = get_text(file)
    subtitles = Subtitles(text, sterilize=True)
    for subtitle in subtitles:
        sys.stdout.write(subtitle.text + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True)
    args = parser.parse_args()
    main(args)
