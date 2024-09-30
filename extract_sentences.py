#!/usr/bin/env python
"""
Extract sentences from SRT file after preprocessing. Writes to STDOUT.
"""
import argparse
import os
import sys

from subtitles import Subtitles

def get_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as e:
        sys.stderr.write(f'UTF-8 decoding failed. Will try latin-1 encoding.')
        with open(filename, 'r', encoding='latin-1') as source_file:
            srt_text = source_file.read()
    return srt_text


def with_file(opts):
    file = os.path.expanduser(opts.file)
    if not os.path.exists(file):
        raise (Exception(f"File path does not exist: {file}"))
    text = get_text(file)
    subtitles = Subtitles(text)
    for subtitle in subtitles:
        sys.stdout.write(subtitle.text + "\n")

def with_dir(opts):
    directory = os.path.expanduser(opts.directory)
    directory = os.path.abspath(directory)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file = os.path.join(root, file)
            if file.lower().endswith('.srt'):
                text = get_text(file)
                subtitles = Subtitles(text)
                output = open(file.replace('.srt', '.sent'), 'w', encoding='utf-8')
                for subtitle in subtitles:
                    output.write(subtitle.text + "\n")
                output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=False)
    parser.add_argument('-d', '--directory', required=False)
    args = parser.parse_args()
    if args.file is not None:
        with_file(args)
    elif args.directory is not None:
        with_dir(args)
    else:
        parser.error("At least -f or -d is required.")
