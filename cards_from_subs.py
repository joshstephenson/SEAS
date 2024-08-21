#!/usr/bin/env python

import argparse
import os
from datetime import datetime
import re

TIMECODE_SEPARATOR      = ' --> '
SENT_BOUNDARIES_REGEX   = r'[\!\.\?]$'
ELLIPSES_REGEX          = r'[.]{3}'
CURLY_BRACKET_REGEX     = r'{[^{]+?}'
SQUARE_BRACKET_REGEX    = r'\[[^\[]+?\]'
MULTIPLE_SPACES         = r'[\s]+'
HTML_REGEX              = r'<[^<]+?>'
CAPTION_REGEX           = r'"[^"]+?"'
PARENTHESES_REGEX       = r'\(.*\)'
LEADING_HYPHENS_REGEX   = r'^-'
SRT_TIME_FORMAT         = '%H:%M:%S,%f'

class Subtitles():
    def __init__(self, text, sterilize=True, strip_captions=True, offset='00:00:00,000', offset_is_negative=False):
        self.index = 0
        self.subtitles = []
        lines = text.split("\n\n")

        # Best to only parse this once, rather than in the Subtitle class
        offset = datetime.strptime(offset, SRT_TIME_FORMAT)

        for line in lines:
            sub_content = line.strip().split("\n")[1:]
            if len(sub_content) == 0:
                continue
            subtitle = Subtitle(sub_content[0], sub_content[1:], offset, offset_is_negative)
            if subtitle.has_content(sterilize, strip_captions):
                self.subtitles.append(subtitle)

        self.subtitles = self.merge_sentences()


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

    def find_pairs(self, target):
        pairs = []
        for sub in self:
            options = target.find(sub)
            pairs.append(SubPair(sub, options))

        if len(pairs) < 2:
            return pairs

        # Resolve overlaps
        resolved = []
        subsequent = pairs.pop(0)
        while len(pairs) > 0:
            current = subsequent
            subsequent = pairs.pop(0)
            commonality = current.commonality_with(subsequent)
            if len(commonality) > 0:
                for opt in commonality:
                    with_current = current.source.overlap(opt)
                    with_subsequent = subsequent.source.overlap(opt)
                    if with_current > with_subsequent:
                        subsequent.remove_option(opt)
                    else:
                        current.remove_option(opt)

            resolved.append(current)
        resolved.append(subsequent)

        # Merge suboptions
        for pair in resolved:
            pair.merge_options()

        return resolved

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
        return SubOptions(options)

    def _find_best(self, sub, options):
        # If more than one subtitle was found, select the one with the largest overlap
        overlap = 0
        best = None
        for option in options:
            _overlap = sub.overlap(option)
            if _overlap > overlap:
                overlap = _overlap
                best = option
        return best

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

class SubOptions():
    def __init__(self, options:[]):
        self.options = options
        self.index = 0

    def find_common(self, other):
        common = []
        for opt in self.options:
            if opt in other.options:
                common.append(opt)
        return common

    def merge(self):
        merged = []
        if len(self.options) > 1:
            first = self.options[0]
            for other in self.options[1:]:
                first.merge(other)
            merged.append(first)
        elif len(self.options):
            merged.append(self.options[0])
        self.options = merged

    def remove(self, item):
        self.options.remove(item)

    def __len__(self):
        return len(self.options)

    def __str__(self):
        return "--".join(str(s) for s in self.options)

    def __iter__(self):
        self.index = -1
        self.current = self.options[self.index]
        return self

    def __next__(self):
        self.index += 1
        if self.index < len(self.options):
            self.current = self.options[self.index]
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

        # remember if we have stripped captions
        self.stripped_captions = False

    def has_content(self, sterilize=True, strip_captions=True):
        if strip_captions and not self.stripped_captions:
            self.text = re.sub(CAPTION_REGEX, '', self.text).strip()
            self.stripped_captions = True

        if sterilize and not self.sterilized:
            # Remove content surrounded by parenthesis
            self.text = re.sub(PARENTHESES_REGEX, "", self.text)

            # Remove HTML content
            self.text = re.sub(HTML_REGEX, '', self.text).strip()

            # Remove content surrounded by curly brackets
            self.text = re.sub(CURLY_BRACKET_REGEX, '', self.text).strip()

            # Remove content surrounded by square brackets
            self.text = re.sub(SQUARE_BRACKET_REGEX, '', self.text).strip()

            # Remove leading hyphens
            self.text = re.sub(LEADING_HYPHENS_REGEX, '', self.text).strip()

            # Remove ellipses
            self.text = re.sub(ELLIPSES_REGEX, '', self.text).strip()

            # Replace multiple whitespace characters with one
            self.text = re.sub(MULTIPLE_SPACES, ' ', self.text).strip()

            self.sterilized = True

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
        # return f'{self.timestring}: {self.text}'
        return self.text

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.timestring == other.timestring

    def __hash__(self):
        return hash(self.timestring)

class SubPair():
    def __init__(self, source:Subtitle, sub_options:SubOptions):
        self.source = source
        self.sub_options = sub_options

    def commonality_with(self, other):
        return self.sub_options.find_common(other.sub_options)

    def remove_option(self, option):
        self.sub_options.remove(option)

    def merge_options(self):
        self.sub_options.merge()

    def __str__(self):
        if len(self.sub_options.options) > 1:
            print(self.source)
            print('--')
            for sub in self.sub_options.options:
                print(sub)
        return f'- {self.source}\n- {self.sub_options}\n'


def main(opts):
    source = os.path.expanduser(opts.source)
    target = os.path.expanduser(opts.target)

    if not os.path.exists(source) or not os.path.exists(target):
        raise(Exception("source or target path does not exist"))

    with open(source, 'r') as sfile:
        stext = sfile.read()
    with open(target, 'r') as tfile:
        ttext = tfile.read()

    source_subs = Subtitles(stext, opts.sterilize, opts.strip_captions)
    target_subs = Subtitles(ttext, opts.sterilize, opts.strip_captions, opts.offset, opts.offset_is_negative)

    pairs = source_subs.find_pairs(target_subs)
    for pair in pairs:
        print(pair)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True)
    parser.add_argument('-t', '--target', required=True)
    parser.add_argument('-o','--offset', required=False, default='00:00:00,000', type=str, help='Time offset between source and target in SRT format. .e.g 00:00:12,500.')
    parser.add_argument('--offset-is-negative', default=False, action='store_true', help='Indicates that the target is ahead of the source.')
    parser.add_argument('--sterilize', action='store_true', default=True, help='Ignores text between parenthesis and HTML.')
    parser.add_argument('--strip-captions', action='store_true', default=True, help='Strip content between quotation markes which is usually captions.')
    opts = parser.parse_args()
    main(opts)
