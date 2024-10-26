#!/usr/bin/env python
"""
Extract sentences from SRT file after preprocessing. Writes to STDOUT.
"""
import argparse
import os

from src.helpers import get_text
from src.languages import Languages
from src.subtitles import Subtitles


def with_file(filename, opts):
    if len(opts.language) == 3:  # language code
        language = Languages.get_language_name(opts.language)
    else:
        language = opts.language
    file = os.path.expanduser(filename)
    if not os.path.exists(file):
        raise (Exception(f"File path does not exist: {file}"))
    text = get_text(file)
    subtitles = Subtitles(text, language=language)
    sent_file = file.replace('.srt', '.sent')
    index_file = file.replace('.srt', '.sent-index')
    output = open(sent_file, 'w', encoding='utf-8')
    index_output = open(index_file, 'w', encoding='utf-8')
    for utterance in subtitles.utterances:
        # if subtitle.has_content():
        # sys.stdout.write(utterance.text + '\n')
        output.write(utterance.text + "\n")
        if opts.index:
            index_output.write(str(sorted([sub.index for sub in utterance.subtitles])) + "\n")
    output.close()
    index_output.close()


def with_dir(opts):
    directory = os.path.expanduser(opts.directory)
    directory = os.path.abspath(directory)
    for root, dirs, files in os.walk(directory):
        for file in files:
            file = os.path.join(root, file)
            if file.lower().endswith('.srt'):
                with_file(file, opts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=False)
    parser.add_argument('-d', '--directory', required=False)
    parser.add_argument('-l', '--language', required=True)
    parser.add_argument('-i', '--index', action="store_true",
                        help="Include a file that prints the indices associated with each sentence. This is used for the annotator.")
    args = parser.parse_args()
    if args.file is not None:
        with_file(args.file, args)
    elif args.directory is not None:
        with_dir(args)
    else:
        parser.error("At least -f or -d is required.")
