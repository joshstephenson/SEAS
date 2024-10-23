#!/usr/bin/env python
"""
Uses linga tools to verify if language in SRT file matches known language code (ISO 639) language codes
Skips firts 50 subtitles becausey they often have annotations and other non-dialogue text.
Collects first 250 (or more) characters and then detects the language.
"""

from lingua import Language, LanguageDetectorBuilder
import argparse
import os
import re
import sys

SUPPORTED_LANGUAGES = [Language.ENGLISH,
             Language.SPANISH,
             Language.FRENCH,
             Language.GERMAN,
             Language.DUTCH,
             Language.ITALIAN,
             Language.SWEDISH,
             Language.JAPANESE,
             Language.KOREAN,
             Language.CHINESE]

LANGUAGE_MAP = {'eng':Language.ENGLISH,
                'spa':Language.SPANISH,
                'fre':Language.FRENCH,
                'ger':Language.GERMAN,
                'dut': Language.DUTCH,
                'ita': Language.ITALIAN,
                'swe': Language.SWEDISH,
                'jpn': Language.JAPANESE,
                'kor': Language.KOREAN,
                'chi': Language.CHINESE}

def detect_language(text):
    detector = LanguageDetectorBuilder.from_languages(*SUPPORTED_LANGUAGES).build()
    language = detector.detect_language_of(text)
    return language

def matches_prediction(language:Language, predicted:str):
    return LANGUAGE_MAP[predicted] == language

def get_sample_text(subtitles):

    # Often the first subtitles can be music or captions or attributions so let's skip the first 50
    if len(subtitles) > 50:
        subtitles = subtitles[50:]

    sample_text = ''
    for subtitle in subtitles:
        # wait until we have a decent amount of text
        if len(sample_text) > 250:
            break
        match = re.search(r'^\d+\n.+\n((.+\n*){1,3})', subtitle, re.MULTILINE)
        if match is not None:
            text = match.groups(1)[0] # it's a nested match
            if len(match.groups()):
                sample_text += match.groups(1)[0]

    return sample_text

def get_language_from_path(path):
    parts = path.split('/')
    return parts[-2]

def get_text_from_file(srt):
    try:
        with open(srt, 'r', encoding='utf-8') as source_file:
            srt_text = source_file.read()
    except UnicodeDecodeError as e:
        # sys.stdout.write(f'ERR: UTF-8 decoding failed. Will try latin-1 encoding.\n')
        with open(srt, 'r', encoding='latin-1') as source_file:
            srt_text = source_file.read()

    return srt_text.strip() # strip whitespace from ends

def process_file(srt, delete_bad=False):
    lang = get_language_from_path(srt)
    text = get_text_from_file(srt)
    assert len(text) > 0
    assert len(lang) == 3

    # Quickly split them
    subtitles = re.split(r'\n{2,}', text)
    sample_text = get_sample_text(subtitles)
    detected = detect_language(sample_text)
    predicted = str(LANGUAGE_MAP[lang]).split('.')[1]
    if detected is not None and matches_prediction(detected, lang):
        sys.stdout.write(f"Language matched prediction of {predicted}.\n")
        exit(0)
    else:
        detected = str(detected).split('.')[1] if detected is not None else "None"
        sys.stderr.write(f"Detected {detected} for file: {srt}\n")
        if delete_bad:
            os.remove(srt)
            sys.stderr.write(f"Removed: {srt}\n")
        exit(1)

def main(opts):
    if opts.directory is not None:
        directory = os.path.expanduser(opts.directory)
        directory = os.path.abspath(directory)
        for root, dirs, files in os.walk(directory):
            for file in files:
                file = os.path.join(root, file)
                if file.lower().endswith('.srt'):
                    process_file(file, opts.delete)
    elif opts.file is not None:
        if opts.file.lower().endswith('.srt'):
            file = os.path.expanduser(opts.file)
            process_file(file, opts.delete)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', required=False)
    parser.add_argument('-f', '--file', required=False)
    parser.add_argument('-D', '--delete', default=False, action='store_true')
    args = parser.parse_args()
    if args.directory is None and args.file is None:
        parser.error("-d or -f must be used for directory or file")
        exit(1)
    main(args)
