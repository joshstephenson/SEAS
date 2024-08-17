#!/usr/bin/env python

import argparse
import os
from datetime import datetime
import re

TIMECODE_SEPARATOR      = ' --> '
SENT_BOUNDARIES_REGEX   = r'[\!\.\?]$'
CURLY_BRACKET_REGEX     = r'{[^{]+?}'
HTML_REGEX              = r'<[^<]+?>'
PARENTHESES_REGEX       = r'\(.*\)'
LEADING_HYPHENS_REGEX   = r'^-'
SRT_TIME_FORMAT         = '%H:%M:%S,%f'

class Subtitles():
    def __init__(self, text, sterilize=False, offset='00:00:00,000', offset_is_negative=False):
        self.index = 0
        self.subtitles = []
        lines = text.split("\n\n")

        # Best to only parse this once, rather than in the Subtitle class
        offset = datetime.strptime(offset, SRT_TIME_FORMAT)

        for line in lines:
            sub_content = line.strip().split("\n")[1:]
            if len(sub_content) == 0:
                continue
            subtitle = self.Subtitle(sub_content[0], sub_content[1:], offset, offset_is_negative)
            if subtitle.has_content(sterilize):
                self.subtitles.append(subtitle)

        self.subtitles = self.merge_sentences()

    def find_pairs(self, target):
        pairs = []
        for sub in target:
            found = self.find(sub)
            if found is not None:
                pairs.append((found, sub))
        return pairs

    def merge_sentences(self):
        """
        Merges subtitles into sentences. If a subtitle does not end with a word boundary,
        the subsequent subtitles will be merged until a word boundary is found.
        :return: merged subtitles
        """
        to_delete = []
        current = None
        found_boundary = True
        for sub in self.subtitles:
            if re.search(SENT_BOUNDARIES_REGEX, sub.text):
                found_boundary = True
            else:
                # print(f'No word boundary for: {sub.text}')
                found_boundary = False
                if current is None:
                    current = sub
            if current is not None and current != sub:
                current.merge(sub)
                to_delete.append(sub)
            if found_boundary:
                current = None

        return [s for s in self.subtitles if s not in to_delete]

    def find(self, other):
        """
        Find the counterpart to a subtitle provided from another language in the current set
        :param other: a target subtitle to find the match
        :return: counterpart subtitle or None
        """

        options = []
        for current in self.subtitles:
            if current.end < other.start:
                continue
            elif current.start > other.end:
                break
            else:
                options.append(current)

        # If more than one subtitle was found, select the one with the largest overlap
        if len(options) > 1:
            overlap = 0
            best = None
            for option in options:
                _overlap = other.overlap(option)
                if _overlap > overlap:
                    overlap = _overlap
                    best = option
            return best
        elif len(options):
            return options[0]
        else:
            return None

    def __iter__(self):
        self.index = -1
        self.current = self.subtitles[self.index]
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.subtitles):
            self.current = self.subtitles[self.index]
            return self.current
        else:
            raise StopIteration

    class Subtitle():
        def __init__(self, timestring, text, offset, offset_is_negative):
            # join multiple lines of text into one line.
            self.text = " ".join(text).strip()

            # Used to display subtitle timecodes
            self.timestring = timestring

            # Used to compare subtitle timecodes
            self.start = 0
            self.end = 0

            # Parse the time code into a number of milliseconds since the start
            self.parsetimecodes(offset, offset_is_negative)

            # remember if we have sterilized so we don't do it again
            self.sterilized = False

        def has_content(self, sterilize=False):
            if sterilize and not self.sterilized:
                # Remove content surrounded by parenthesis
                self.text = re.sub(PARENTHESES_REGEX, "", self.text)

                # Remove HTML content
                self.text = re.sub(HTML_REGEX, '', self.text).strip()

                # Remove content surrounded by curly brackets
                self.text = re.sub(CURLY_BRACKET_REGEX, '', self.text).strip()

                # Remove leading hyphens
                self.text = re.sub(LEADING_HYPHENS_REGEX, '', self.text).strip()

            return len(self.text) > 0

        def parsetimecodes(self, offset, offset_is_negative):
            """
            Turn timestrings like '01:23:45,678' into an integer offset milliseconds since movie start
            """
            def _parse(timestring):
                pt = datetime.strptime(timestring, SRT_TIME_FORMAT)
                if offset_is_negative:
                    microsecond = pt.microsecond - offset.microsecond
                    second = pt.second - offset.second
                    minute = pt.minute - offset.minute
                    hour = pt.hour - offset.hour
                else:
                    microsecond = pt.microsecond + offset.microsecond
                    second = pt.second + offset.second
                    minute = pt.minute + offset.minute
                    hour = pt.hour + offset.hour
                return microsecond + (second + minute * 60 + hour * 3600) * 1000000

            parts = self.timestring.split(TIMECODE_SEPARATOR)
            self.start = _parse(parts[0])
            self.end = _parse(parts[1])

        def overlap(self, other):
            """
            Find the duration of time two subtitles overlap with each other
            :param other: the other subtitle to compare with self
            :return: duration of time two subtitles overlap with each other
            """
            start = max(self.start, other.start)
            end = min(self.end, other.end)
            return end - start

        def merge(self, other):
            """
            Merge another subtitle with this subtitle. Used when a sentence is spread across multiple subtitles.
            :param other: other subtitle to merge
            """
            self.text += " " + other.text
            self.end = other.end
            self.timestring = self.timestring.split(TIMECODE_SEPARATOR)[0] + TIMECODE_SEPARATOR + other.timestring.split(TIMECODE_SEPARATOR)[1]

        def __str__(self):
            return f'{self.timestring}: {self.text}'


def main(opts):
    source = os.path.expanduser(opts.source)
    target = os.path.expanduser(opts.target)

    if not os.path.exists(source) or not os.path.exists(target):
        raise(Exception("source or target path does not exist"))

    with open(source, 'r') as sfile:
        stext = sfile.read()
    with open(target, 'r') as tfile:
        ttext = tfile.read()

    source_subs = Subtitles(stext, opts.sterilize)
    target_subs = Subtitles(ttext, opts.sterilize, opts.offset, opts.offset_is_negative)

    pairs = source_subs.find_pairs(target_subs)
    print(f'Found {len(pairs)} subtitle pairs')
    for pair in pairs:
        print(pair[0].text)
        print(pair[1].text + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--offset', required=False, default='00:00:00,000', type=str, help='Time offset between source and target in SRT format. .e.g 00:00:12,500.')
    parser.add_argument('--offset-is-negative', default=False, action='store_true', help='Indicates that the target is ahead of the source.')
    parser.add_argument('--sterilize', action='store_true', default=False, help='Ignores text between parenthesis and HTML.')
    opts = parser.parse_args()
    main(opts)
