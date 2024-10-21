#!/usr/bin/env python

import argparse
import sys
from difflib import SequenceMatcher

from pandas import DataFrame
from Levenshtein import distance
from nltk import everygrams
from src.alignment import Alignment
from src.config import Config

SOFT_THRESHOLD = 0.05

class TermColor:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    # Yellow = "\033[33m"
    # Blue = "\033[34m"
    # Magenta = "\033[35m"
    # Cyan = "\033[36m"
    # Gray = "\033[37m"
    # White = "\033[97m"

def find_most_similar(candidate: Alignment, group: [Alignment]):
    """
    Find the most likely alignment based on ngrams
    """
    best = None
    best_overlap = 0
    for alignment in group:
        source_match = SequenceMatcher(None, candidate.source, alignment.source).find_longest_match()
        target_match = SequenceMatcher(None, candidate.target, alignment.target).find_longest_match()
        overlap = source_match.size + target_match.size
        if overlap > best_overlap:
            best_overlap = overlap
            best = alignment

    return best


def meets_accuracy_requirement(prediction: Alignment, gold: Alignment, strict=True):
    """
    checks if prediction source and gold source have 95% accuracy based on edit distance
    :param strict: Means one side has to match exactly.
    """

    def _meets(prd: str, gld: str):
        if prd == gld:
            return True
        if len(prd) == 0 or len(gld) == 0:
            return False
        longer = max(len(prd), len(gld))
        edit_distance = distance(prd, gld)
        normalized = edit_distance / longer
        qualifies = normalized <= SOFT_THRESHOLD
        # print(normalized)
        # print(prediction, '--', gold)
        # print(f'longer: {longer}, edit_distance: {edit_distance}, normalized: {normalized}, qualifies: {qualifies}')
        return qualifies

    if not strict:
        first, second = _meets(prediction.source, gold.source), _meets(prediction.target, gold.target)
        return first and second
    assert prediction.source is not None and prediction.target is not None
    if prediction.source != gold.source and prediction.target != gold.target:
        return False
    elif prediction.source != gold.source:
        return _meets(prediction.source, gold.target)
    elif prediction.target != gold.target:
        return _meets(prediction.target, gold.target)


def adjust_for_soft_scoring(gold: [Alignment],
                            predictions: [Alignment],
                            false_neg: [Alignment],
                            true_pos: [Alignment],
                            strict=True):
    """
    Move items from false_pos to true_pos if 95% accuracy based on MED
    :returns: nothing, but it does modify the contents of the passed lists
    """
    qualify = []

    for fp in false_neg:
        for g in gold:
            if meets_accuracy_requirement(fp, g, strict):
                qualify.append(fp)
                break
            # if fp.source == g.source and fp.target != g.target:
            #     # print(f'\nSources were aligned: {fp.source} -- {g.source}')
            #     # print(f'Targets were not: {fp.target} -- {g.target}')
            #     if meets_accuracy_requirement(fp.target, g.target):
            #         qualify.append(fp)
            #         break
            # elif fp.source != g.source and fp.target == g.target:
            #     # print(f'\nTargets were aligned: {fp.target} -- {g.target}')
            #     # print(f'Sources were not: {fp.source} -- {g.source}')
            #     if meets_accuracy_requirement(fp.source, g.source):
            #         qualify.append(fp)
            #         break

    for q in qualify:
        false_neg.remove(q)
        true_pos.append(q)


def print_results(gold, predictions, soft_scoring=False, print_pp=False, print_fp=False, print_fn=False):
    true_pos = [a for a in predictions if a in gold]
    false_pos = [a for a in predictions if a not in gold]
    false_neg = [a for a in gold if a not in predictions]

    if soft_scoring:  # FIXME: this doesn't work
        print("Soft scoring doesn't work. FIXME.")
        exit()
        # adjust_for_soft_scoring(gold, predictions, false_neg, true_pos)
    gold_length = len(gold)
    true_pos_length = len(true_pos)
    len_predictions = len(predictions)
    false_pos_length = len(false_pos)
    false_neg_length = len(false_neg)

    precision = true_pos_length / (true_pos_length + false_pos_length)
    recall = true_pos_length / (true_pos_length + false_neg_length)
    f1 = 2 * precision * recall / (precision + recall)

    # Output as TSV for easy parsing by Bash
    print('True Positives\tFalse Negatives\tFalse Positives\tRecall\tPrecision\tF1')
    print(f'{true_pos_length}\t{false_neg_length}\t{false_pos_length}\t{recall}\t{precision}\t{f1}')

    # cm = DataFrame([[true_pos_length, false_pos_length, precision],
    #                 [false_neg_length, 0, 0],
    #                 [recall, 0, 0]],
    #                columns=['Positive', 'Negative', 'Precision'])
    # cm.index = ['Positive', 'Negative', 'Recall']
    # print(cm)
    if print_fp:
        print_false_positives(false_pos, gold)
    if print_fn:
        print_false_negatives(false_neg, predictions)
    if print_pp:
        print_true_positives(true_pos)


def print_true_positives(true_pos):
    for tp in true_pos:
        print(f'{tp.source}\n{TermColor.GREEN}{tp.target}{TermColor.RESET}\n')


def print_false_positives(false_positives, gold):
    print("\n################")
    print("False Positives:\n")
    for fp in false_positives:
        partner = find_most_similar(fp, gold)
        # longest_source = max(len(partner.source), len(fp.source))
        # print(f'{fp.source} <-> {fp.target}')
        # print(f'{TermColor.GREEN}{partner.source.rjust(longest_source, " ")} <-> {partner.target}{TermColor.RESET}\n')
        if fp.source != partner.source:
            print(f'{fp.source}\n{TermColor.GREEN}{partner.source}{TermColor.RESET}\n')
        if fp.target != partner.target:
            print(f'{fp.target}\n{TermColor.GREEN}{partner.target}{TermColor.RESET}\n')


def print_false_negatives(false_negatives, predictions):
    print("\n################")
    print("False Negatives:\n")
    for fn in false_negatives:
        partner = find_most_similar(fn, predictions)
        if fn.source != partner.source:
            print(f'{partner.source}\n{TermColor.GREEN}{fn.source}{TermColor.RESET}')
        if fn.target != partner.target:
            print(f'{partner.target}\n{TermColor.GREEN}{fn.target}{TermColor.RESET}\n')



def main(opts):
    with open(opts.gold_file, "r") as gold_file:
        gold_lines = gold_file.read().strip()
    with open(opts.alignments_file, "r") as alignments_file:
        alignments_lines = alignments_file.read().strip()

    prediction_alignments = alignments_lines.split("\n\n")
    gold_alignments = gold_lines.split('\n\n')

    try:
        predictions = [Alignment(alignment[0].strip(), alignment[1].strip()) for alignment in
                       [a.split('\n') for a in prediction_alignments]]
    except Exception as _:
        sys.stderr.write("Error parsing predictions file. The problem appears to be:\n")
        for i, a in enumerate(prediction_alignments):
            if len(a.split('\n')) != 2:
                sys.stderr.write(f'Line {i}: {a}\n')
        exit(1)

    try:
        gold = [Alignment(alignment[0].strip(), alignment[1].strip()) for alignment in
                [a.split('\n') for a in gold_alignments]]
    except Exception as _:
        sys.stdout.write("Error parsing gold file. The problem appears to be:\n")
        for i, a in enumerate(gold_alignments):
            if len(a.split('\n')) != 2:
                sys.stderr.write(str(len(a.split('\n'))) + ': ')
                sys.stderr.write(f'Line {i}: {a}\n')
        exit(1)

    print_results(gold, predictions, opts.soft, opts.true_positives, opts.false_positives, opts.false_negatives)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gold-file', required=True)
    parser.add_argument('-a', '--alignments-file', required=True)
    parser.add_argument('-s', '--soft', action='store_true', default=Config.UseSoftScoring,
                        help='Use soft scoring from Buck & Koehn 2016')
    parser.add_argument('-fn', '--false-negatives', action='store_true', help='Print false negatives.')
    parser.add_argument('-fp', '--false-positives', action='store_true', help='Print false positives.')
    parser.add_argument('-tp', '--true-positives', action='store_true', help='Print true positives.')
    args = parser.parse_args()

    # test1 = Alignment('Today was a good day.', '-Hoy fue un buen dia.', [], [])
    # gold1 = Alignment('Today was a good day.', 'Hoy fue un buen dia.', [], [])
    # print(meets_accurace_requirement(test1, gold1))
    main(args)
