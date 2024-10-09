#!/usr/bin/env python
import argparse
import sys

def main(opts):
    sent_file = opts.sent_file
    align_file = opts.align_file

    try:
        with open(sent_file, 'r') as sf:
            lines = [a.lower() for a in sf.readlines()]
    except FileNotFoundError:
        print(f"Error: File {sent_file} not found.")
        sys.exit(1)

    # Read the alignments file content
    try:
        with open(align_file, 'r') as af:
            alignments = af.read().lower()
    except FileNotFoundError:
        print(f"Error: File {align_file} not found.")
        sys.exit(1)

    alignment_lines = alignments.splitlines()
    # Process each line from the sentence file
    matches = 0
    for line in lines:
        line = line.strip()  # Remove newline characters

        # Print occurrences of the line in the alignments file
        matching_lines = []
        if line in alignments:
            matching_lines = [align for align in alignments.splitlines() if line in align]
        if opts.verbose:
            if len(matching_lines) > 0:
                matches += 1
                print(f'MATCH {line}\n\t{matching_lines}')
            else:
                print(f'NO MATCH {line}')

    print(f"Matches: {matches}, Original lines: {len(lines)}, Aligned lines: {int(len(alignment_lines)/3)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process a sentence file and an alignments file.")
    parser.add_argument('-s', '--sent-file', help='Path to the sentence file')
    parser.add_argument('-a', '--align-file', help='Path to the alignments file')
    parser.add_argument('--strict', help='Strict mode', action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose mode', action='store_true')

    # Parse arguments
    args = parser.parse_args()
    main(args)