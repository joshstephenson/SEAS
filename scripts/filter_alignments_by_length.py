#!/usr/bin/env python

import argparse
import sys

import regex


def main(opts):
    with open(opts.file, 'r', encoding='latin-1') as source_file:
        # read 2 lines
        while True:
            lines = [source_file.readline().strip() for _ in range(2)]
            if len(lines[0]) > opts.min_length and len(lines[1]) > opts.min_length:
                sys.stdout.write('\n'.join(lines) + '\n\n')

            empty = source_file.readline().strip()
            assert len(empty) == 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True)
    parser.add_argument('-l', '--min-length', default=30, type=int)
    args = parser.parse_args()
    main(args)
