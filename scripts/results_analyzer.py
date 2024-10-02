#!/usr/bin/env python

import argparse
import os
from nltk import everygrams


class Data:
    def __init__(self, files):
        self.load_files(files)

        set1 = set(self.left_alignments)
        set2 = set(self.right_alignments)

        self.disagreements = set1.difference(set2)
        self.agreements = set1.intersection(set2)
        self.gold = list(self.agreements)
        self.left_stats = [len(self.left_alignments), len(self.left_alignments)]
        self.right_stats = [len(self.right_alignments), len(self.right_alignments)]
        print(self.left_stats)
        print(self.right_stats)

    def load_files(self, files):
        self.left_label = os.path.basename(files[0])
        self.right_label = os.path.basename(files[1])
        file1 = open(files[0], 'r', encoding='utf-8')
        file2 = open(files[1], 'r', encoding='utf-8')
        alignments1 = file1.read()
        alignments2 = file2.read()
        file1.close()
        file2.close()
        # each alignment should be 2 lines
        self.left_alignments = alignments1.split('\n\n')
        self.right_alignments = alignments2.split('\n\n')

    def find_candidate(self, target, candidates):
        """
        Find the most likely alignment based on ngrams
        """
        target_grams = list(everygrams(target.split(), max_len=2))
        best = None
        best_overlap = 0
        for line in candidates:
            candidate_grams = list(everygrams(line.split(), max_len=2))
            overlap = []  # we don't want uniq so a set won't do
            for gram in target_grams:
                if gram in candidate_grams:
                    overlap.append(gram)
            if len(overlap) > best_overlap:
                best_overlap = len(overlap)
                best = line
        return best

    def add_gold_to_left(self, left, right):
        self.gold.append(left)
        self.disagreements.remove(right)
        # right side was wrong
        self.right_stats[1] += 1

    def add_gold_to_right(self, left, right):
        self.gold.append(right)
        self.disagreements.remove(right)
        # left side was wrong
        self.left_stats[1] += 1

    def both_wrong(self, left, right):
        self.disagreements.remove(right)
        self.left_stats[1] += 1
        self.right_stats[1] += 1

    def stats_str(self):
        left_score = self.left_stats[0] / self.left_stats[1] * 100.0
        right_score = self.right_stats[0] / self.right_stats[1] * 100.0
        return f'{self.left_label}: {left_score:.2f}. {self.right_label}: {right_score:.2f}'


def main(opts):
    data = Data(opts.files)

    while len(data.disagreements):
        left = data.disagreements.pop()
        right = data.find_candidate(left, data.disagreements)
        if right is None:
            print(f'Could not find a candidate for "{left}". Skipping...')
        else:
            print(data.stats_str())
            print("\n", left, "\n---------\n", right)
            answer = input("1,2,3")
            match answer:
                case '1':
                    data.add_gold_to_left(left, right)
                case '2':
                    data.add_gold_to_right(left, right)
                case _:
                    data.both_wrong(left, right)

    output = open('gold.txt', 'w', encoding='utf-8')
    for g in data.gold:
        output.write(g + "\n\n")
    output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', required=True, nargs='+', help='2 alignment files to compare')
    args = parser.parse_args()
    if len(args.files) != 2:
        parser.error('Must provide 2 alignment files')
    main(args)
