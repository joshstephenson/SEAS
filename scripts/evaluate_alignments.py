#!/usr/bin/env python

import argparse
from pandas import DataFrame
from Levenshtein import distance

from src.alignment import Alignment


def print_results(gold, predictions):
    true_pos = [a for a in predictions if a in gold]
    false_pos = [a for a in predictions if a not in gold]
    false_neg = [a for a in gold if a not in predictions]

    gold_length = len(gold)
    true_pos_length = len(true_pos)
    len_predictions = len(predictions)
    false_pos_length = len(false_pos)
    false_neg_length = len(false_neg)

    precision = true_pos_length / len_predictions
    recall = true_pos_length / (true_pos_length + false_neg_length)

    cm = DataFrame([[true_pos_length],
                    [false_neg_length],
                    [recall]],
                   columns=['Positive'])
    cm.index = ['Positive', 'Negative', 'Recall']
    print(cm)


def main(opts):
    with open(opts.gold_file, "r") as gold_file:
        gold_lines = gold_file.read().strip()
    with open(opts.alignments_file, "r") as alignments_file:
        alignments_lines = alignments_file.read().strip()

    prediction_alignments = alignments_lines.split("\n\n")
    gold_alignments = gold_lines.split('\n\n')

    try:
        predictions = [Alignment(alignment[0], alignment[1]) for alignment in [a.split() for a in prediction_alignments]]
    except Exception as _:
        print("Error parsing predictions file. The problem appears to be:")
        for i, a in enumerate(prediction_alignments):
            if len(a.split()) != 2:
                print(f'Line {i}: {a}')

    try:
        gold = [Alignment(alignment[0], alignment[1]) for alignment in [a.split() for a in gold_alignments]]
    except Exception as _:
        print("Error parsing predictions file. The problem appears to be:")
        for i, a in enumerate(gold_alignments):
            if len(a.split()) != 2:
                print(f'Line {i}: {a}')

    print_results(gold, predictions)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gold-file', required=True)
    parser.add_argument('-a', '--alignments-file', required=True)
    args = parser.parse_args()
    main(args)