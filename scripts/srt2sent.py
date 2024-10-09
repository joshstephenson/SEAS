#!/usr/bin/env python
"""
Extract sentences from SRT file after preprocessing. Writes to STDOUT.
"""
import argparse
import os
import sys
import regex
from helpers import sterilize, get_text

from subtitles import Subtitles

def with_file(opts):
    file = os.path.expanduser(opts.file)
    if not os.path.exists(file):
        raise (Exception(f"File path does not exist: {file}"))
    text = get_text(file)
    if opts.raw:
        text = regex.sub(r'\r', '', text)
        # Split on 2 or more lines in a row
        sub_contents = regex.split(r'\n{2,}', text)
        for sub_text in sub_contents:
            content = "\n".join(sub_text.splitlines()[2:])
            content = sterilize(content)
            if len(content):
                sys.stdout.write(content + '\n')
    else:
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
                sent_file = file.replace('.srt', '.sent')
                output = open(sent_file, 'w', encoding='utf-8')
                for subtitle in subtitles:
                    output.write(subtitle.text + "\n")
                output.close()
                sys.stdout.write(sent_file + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=False)
    parser.add_argument('-d', '--directory', required=False)
    parser.add_argument('-r', '--raw', action="store_true")
    args = parser.parse_args()
    if args.file is not None:
        with_file(args)
    elif args.directory is not None:
        with_dir(args)
    else:
        parser.error("At least -f or -d is required.")
