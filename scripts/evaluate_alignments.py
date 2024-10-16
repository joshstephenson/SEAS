#!/usr/bin/env python

import argparse
from pandas import DataFrame
from Levenshtein import distance

from src.alignment import Alignment

SOFT_THRESHOLD = 0.05


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


def print_results(gold, predictions, soft_scoring=False):
    true_pos = [a for a in predictions if a in gold]
    false_pos = [a for a in predictions if a not in gold]
    false_neg = [a for a in gold if a not in predictions]

    print(f'True positives before: {len(true_pos)}')
    if soft_scoring:
        adjust_for_soft_scoring(gold, predictions, false_neg, true_pos)
    print(f'True positives after: {len(true_pos)}')
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
        predictions = [Alignment(alignment[0].strip(), alignment[1].strip()) for alignment in [a.split('\n') for a in prediction_alignments]]
    except Exception as _:
        print("Error parsing predictions file. The problem appears to be:")
        for i, a in enumerate(prediction_alignments):
            if len(a.split()) != 2:
                print(f'Line {i}: {a}')

    try:
        gold = [Alignment(alignment[0].strip(), alignment[1].strip()) for alignment in [a.split('\n') for a in gold_alignments]]
    except Exception as _:
        print("Error parsing predictions file. The problem appears to be:")
        for i, a in enumerate(gold_alignments):
            if len(a.split()) != 2:
                print(f'Line {i}: {a}')

    print_results(gold, predictions, opts.soft)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gold-file', required=True)
    parser.add_argument('-a', '--alignments-file', required=True)
    parser.add_argument('-s', '--soft', action='store_true', help='Use soft scoring from Buck & Koehn 2016')
    args = parser.parse_args()

    # test1 = Alignment('Today was a good day.', '-Hoy fue un buen dia.', [], [])
    # gold1 = Alignment('Today was a good day.', 'Hoy fue un buen dia.', [], [])
    # print(meets_accurace_requirement(test1, gold1))
    main(args)