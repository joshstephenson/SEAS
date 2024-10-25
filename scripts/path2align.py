#!/usr/bin/env python
import argparse
import re
import numpy as np
import sys
"""
This script generates aligned sentences using 3 files:
- A file of sentences from the source Subtitle file (*.sent file)
- A file of sentences from the target Subtitle file (*.sent file)
- A file of alignments from either vecalign or sentalign (*.path)
"""

def get_ids_from_str(id_string):
    ids = re.findall(r'\d+', id_string)
    return [int(i) for i in ids]


def main(opts):
    path_file = open(opts.path_file, 'r', encoding='utf-8')
    source_file = open(opts.source, 'r', encoding='utf-8')
    target_file = open(opts.target, 'r', encoding='utf-8')
    paths = [a.strip() for a in path_file.readlines()]
    path_file.close()

    # Using np arrays because they allow passing arrays as indices
    source_sentences = np.array([l.strip() for l in source_file.readlines()])
    target_sentences = np.array([l.strip() for l in target_file.readlines()])

    source_file.close()
    target_file.close()

    for path in paths:
        parts = path.split(':')
        source_idx = get_ids_from_str(parts[0])
        target_idx = get_ids_from_str(parts[1])
        # sound_idx and target_idx are arrays
        source_sentence = opts.join_token.join(source_sentences[source_idx])
        target_sentence = opts.join_token.join(target_sentences[target_idx])
        if opts.verbose:
            if len(source_sentence) == 0:
                source_sentence = "*" * len(target_sentence)
            elif len(target_sentence) == 0:
                target_sentence = "*" * len(source_sentence)
            sys.stdout.write(f'{source_sentence}\n{target_sentence}' + "\n\n")
        else:
            if len(source_sentence) and len(target_sentence):
                sys.stdout.write(f'{source_sentence}\n{target_sentence}' + "\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Source .sent file.')
    parser.add_argument('-t', '--target', required=True, help='Target .sent file.')
    parser.add_argument('-p', '--path-file', required=True, help='.path file with alignments')
    parser.add_argument('-j', '--join-token', default=' ', help="The token to join multiple sentences. Default is space.")
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Print alignments even when they're one-sided")
    args = parser.parse_args()
    main(args)