#!/usr/bin/env python
import argparse
import re
import numpy as np
import sys

def get_ids_from_str(id_string):
    ids = re.findall(r'\d+', id_string)
    return [int(i) for i in ids]


def main(opts):
    alignments_file = open(opts.alignments, 'r', encoding='utf-8')
    source_file = open(opts.source, 'r', encoding='utf-8')
    target_file = open(opts.target, 'r', encoding='utf-8')
    alignments = [a.strip() for a in alignments_file.readlines()]
    alignments_file.close()
    source_sentences = np.array([l.strip() for l in source_file.readlines()])
    source_file.close()
    target_sentences = np.array([l.strip() for l in target_file.readlines()])
    target_file.close()

    for line in alignments:
        parts = line.split(':')
        source_idx = get_ids_from_str(parts[0])
        target_idx = get_ids_from_str(parts[1])
        source_sentence = " ".join(source_sentences[source_idx])
        target_sentence = " ".join(target_sentences[target_idx])
        # sys.stdout.write(f'{parts[0]}:{parts[1]}' + "\n")
        if len(source_sentence) and len(target_sentence):
            sys.stdout.write(f'{source_sentence}\n{target_sentence}' + "\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True)
    parser.add_argument('-t', '--target', required=True)
    parser.add_argument('-a', '--alignments', required=True)
    args = parser.parse_args()
    main(args)