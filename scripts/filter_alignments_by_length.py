#!/usr/bin/env python

import argparse
import sys
from itertools import islice

import regex


def main(opts):
    file = sys.stdin if opts.file is None else open(opts.file, 'r', encoding='latin-1')
    for lines in iter(lambda: list(islice(file, 3)), []):
        # Read 2 lines

        if len(lines[0]) >= opts.min_length and len(lines[1]) >= opts.min_length:
            if opts.max_length is not None:
                if len(lines[0]) <= opts.max_length and len(lines[1]) <= opts.max_length:
                    sys.stdout.write(''.join(lines))
            else:
                sys.stdout.write(''.join(lines))

        # Then read an empty line
        assert len(lines[2].strip()) == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=False)
    parser.add_argument('-min', '--min-length', default=30, type=int)
    parser.add_argument('-max', '--max-length', required=False, type=int)
    args = parser.parse_args()
    main(args)
