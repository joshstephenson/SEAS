#!/usr/bin/env python

import argparse
import os
from datetime import datetime
import regex
import string
from nltk.tokenize import sent_tokenize

TIMECODE_SEPARATOR = ' --> '
SENT_BOUNDARIES_REGEX = r'[\!\.\?]$'
ELLIPSES_REGEX = r'[.]{3}'
CURLY_BRACKET_REGEX = r'{[^{]+?}'
SQUARE_BRACKET_REGEX = r'\[[^\[]+?\]'
MULTIPLE_SPACES = r'[\s]+'
HTML_REGEX = r'<[^<]+?>'
CAPTION_REGEX = r'"[^"]+?"'

# Matches one word with a colon
CHARACTER_MARKER_REGEX = r'[[:upper:]]*[:]+\W+'

# Matches 2 or more words in all CAPS along with adjacent punctuation
CAPITALS_REGEX = r'([A-Z]{2,}[,:.]?\s){2,}[:]?' #
PARENTHESES_REGEX = r'\(.*\)'
LEADING_HYPHENS_REGEX = r'^-'
SRT_TIME_FORMAT = '%H:%M:%S,%f'


class Subtitle:
    """
    Subtitle represents a single visual text element in a movie in just one language
    """
    def __init__(self, timestring, text, offset, offset_is_negative):
        self.offset = offset
        self.offset_is_negative = offset_is_negative

        # join multiple lines of text into one line if necessary
        self.text = text if type(text) is str else " ".join(text).strip()

        # Used to display subtitle timecodes
        self.timestring = timestring

        # Used to compare subtitle timecodes
        self.start = 0
        self.end = 0

        # Parse the time code into a number of milliseconds since the start
        self.parse_time_codes(offset, offset_is_negative)

        # remember if we have sterilized so we don't do it again
        self.sterilized = False

    def has_content(self, sterilize=True, strip_captions=True):
        """
        :param sterilize: boolean to strip HTML and special characters
        :param strip_captions: boolean to strip captions (content between quotation marks)
        :returns: True if text length is not zero after sterilizaton when appropriate
        """
        self.text = self.text.replace('\n', ' ')
        if sterilize and not self.sterilized:
            if strip_captions:
                self.text = regex.sub(CAPTION_REGEX, '', self.text)
                self.text = regex.sub(CHARACTER_MARKER_REGEX, '', self.text)
                self.text = regex.sub(CAPITALS_REGEX, '', self.text)

            # Remove content surrounded by parenthesis
            self.text = regex.sub(PARENTHESES_REGEX, "", self.text)

            # Remove HTML content
            self.text = regex.sub(HTML_REGEX, '', self.text)

            # Remove content surrounded by curly brackets
            self.text = regex.sub(CURLY_BRACKET_REGEX, '', self.text)

            # Remove content surrounded by square brackets
            self.text = regex.sub(SQUARE_BRACKET_REGEX, '', self.text)

            # Remove leading hyphens
            self.text = regex.sub(LEADING_HYPHENS_REGEX, '', self.text)

            # Remove ellipses
            self.text = regex.sub(ELLIPSES_REGEX, '', self.text)

            # Replace multiple whitespace characters with one
            self.text = regex.sub(MULTIPLE_SPACES, ' ', self.text).strip()

            self.sterilized = True

        return len(self.text) > 0

    def parse_time_codes(self, offset, offset_is_negative):
        """
        Turn timestrings like '01:23:45,678' into an integer offset milliseconds since movie start
        :param offset: offset is a datetime object
        :param offset_is_negative: boolean to indicate whether above offset is negative
        :return: an integer duration since video start
        """

        def _parse_timestring(timestring):
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
        self.start = _parse_timestring(parts[0])
        self.end = _parse_timestring(parts[1])

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
        self.timestring = self.timestring.split(TIMECODE_SEPARATOR)[0] + TIMECODE_SEPARATOR + \
                          other.timestring.split(TIMECODE_SEPARATOR)[1]

    def __str__(self):
        return self.text

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.timestring == other.timestring

    def __hash__(self):
        return hash(self.timestring)


class SubOptions:
    """
    SubOptions is a class that acts as a wrapper for a list of subtitles.
    It facilitates finding overlap with other lists of subtitles and merging those subtitles when necessary.
    """
    def __init__(self, options: [Subtitle]):
        self.options = options
        self.index = 0

    def find_common(self, other):
        """
        Find target subtitles that are common between this object and other
        :return: list of target subtitles (typically just one)
        """
        common = []
        for opt in self.options:
            if opt in other.options:
                common.append(opt)
        return common

    def merge(self):
        """
        Merge all target subtitles (target options) into one
        """
        if len(self.options) == 0:
            return

        merged = []
        first = self.options[0]
        merged.append(first)
        for other in self.options[1:]:
            first.merge(other)
        self.options = merged

    def remove(self, item):
        self.options.remove(item)

    def sentences(self) -> [str]:
        text = " ".join(str(s) for s in self.options)
        sentences = sent_tokenize(text)
        return sentences

    def remove_last_sentence(self) -> Subtitle:
        opt: Subtitle = self.options[-1]
        sentence = self.sentences()[-1]
        opt.text = opt.text.replace(sentence, '')
        sub = Subtitle(opt.timestring, sentence, opt.offset, opt.offset_is_negative)
        return sub

    def add_option(self, option: Subtitle):
        self.options.append(option)

    def __len__(self):
        return len(self.options)

    def __str__(self):
        return "--".join(str(s) for s in self.options).strip()

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


class SubPair:
    """
    SubPair is a class that has a one-to-many relationship between a source subtitle and target subtitles.
    This is due to the fact that subtitle timecodes often overlap between languages.
    This class is also used as a linked list to walk the subtitle pairs and resolve conflicts between them
    and their previous and subsequent subtitle pairs by moving, merging or altering subtitles.
    """
    def __init__(self, previous, source: Subtitle, sub_options: SubOptions):
        self.source = source
        self.sub_options = sub_options
        self.flagged_for_delete = False
        self.previous = previous
        self.subsequent = None

    def commonality_with(self, other):
        return self.sub_options.find_common(other.sub_options)

    def remove_option(self, option):
        self.sub_options.remove(option)

    def merge_options(self):
        self.sub_options.merge()

    def has_no_target(self):
        return len(self.sub_options) == 0

    def is_longer_than(self, limit=30) -> bool:
        if self.has_no_target():
            return False
        if len(str(self.source)) > limit and len(str(self.sub_options)) > limit:
            return True
        return False

    def target_sentences(self):
        sentences = self.sub_options.sentences()
        return [s for s in sentences if len(s)]

    def pop_last_sentence_as_subtitle(self) -> Subtitle:
        sentence = self.sub_options.remove_last_sentence()
        return sentence

    def add_option(self, option: Subtitle):
        self.sub_options.add_option(option)

    def append_sentence_to_source(self, sentence: str):
        self.source.text = self.source.text + ' ' + sentence

    def resolve_conflicts(self, sterilize=True, strip_captions=True):
        # Resolve situations where two subsequent source subtitles have overlap with the same target subtitle
        # by assigning the target sub to the source with the greatest overlap
        commonality = self.commonality_with(self.subsequent)
        if len(commonality) > 0:
            for opt in commonality:
                with_current = self.source.overlap(opt)
                with_subsequent = self.subsequent.source.overlap(opt)
                if with_current > with_subsequent:
                    self.subsequent.remove_option(opt)
                else:
                    self.remove_option(opt)

            # Sometimes a subtitle has no targets, most likely because the previous subtitle "swallowed" its target
            # So we should merge the sources
            if self.has_no_target():
                if self.previous is not None and len(self.previous.target_sentences()) > 1:
                    sub = self.previous.pop_last_sentence_as_subtitle()
                    if sub.has_content(sterilize, strip_captions):
                        self.add_option(sub)

            if self.subsequent.has_no_target:
                if len(self.target_sentences()) > 1:
                    sub = self.pop_last_sentence_as_subtitle()
                    if sub.has_content(sterilize, strip_captions):
                        self.subsequent.add_option(sub)

    def __str__(self):
        return f'{self.source}\n{self.sub_options}\n'


class Subtitles:
    """
    Subtitles is a class that takes in a body of text represent an SRT file and stores a list of subtitles associated
    with a single language. It also allows merging of sentences and aligning subtitles from another language based
    on timecodes.
    """
    def __init__(self, text, sterilize=True, strip_captions=True, offset='00:00:00,000', offset_is_negative=False):
        self.index = 0
        self.subtitles = []
        lines = regex.split(r'\n{2,}', text)

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
        for sub in self.subtitles:
            if regex.search(SENT_BOUNDARIES_REGEX, sub.text):
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

    def align(self, target):
        """
        Aligns the subtitles in target by iterating over the subtitles in self and looking for a match in target
        based on timecodes. The targets found might be multiple in which case the SubPair object will have one source
        and multiple sub_options. Those will be resolved in this function as well (if possible) by selecting the
        options with the greatest overlap, compared to the previous subtitle.
        :param target: Another Subtitles object for corresponding language
        :return: a list of SubPair objects
        """
        pairs = []
        previous = None
        for sub in self:
            sub_pair = SubPair(previous, sub, target.find(sub))
            pairs.append(sub_pair)
            if previous is not None:
                previous.subsequent = sub_pair
            previous = sub_pair

        # Resolve overlaps
        resolved = []
        current = pairs[0]
        while current.subsequent is not None:
            current.resolve_conflicts()
            if not current.flagged_for_delete:
                resolved.append(current)
            current = current.subsequent
        resolved.append(current)

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

    def _find_best(self, source, options):
        """
        If more than one subtitle was found, select the one with the largest overlap
        :returns: option with the largest overlap with source subtitle
        """
        overlap = 0
        best = None
        for option in options:
            _overlap = source.overlap(option)
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
    source_subs = Subtitles(source_text, opts.sterilize, opts.strip_captions)
    target_subs = Subtitles(target_text, opts.sterilize, opts.strip_captions, opts.offset, opts.offset_is_negative)

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
    parser.add_argument('--sterilize', action='store_true', default=True,
                        help='Ignores text between HTML, parenthesis, brackets and other special characters.')
    parser.add_argument('--strip-captions', action='store_true', default=True,
                        help='Strip content between quotation marks which is usually captions.')
    parser.add_argument('--strict', default=30, type=int, help='Don\'t print out subtitle pairs if they\'re shorter than certain length.')
    args = parser.parse_args()
    main(args)
