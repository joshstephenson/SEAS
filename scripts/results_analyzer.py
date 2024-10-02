#!/usr/bin/env python

import argparse
import os
from nltk import everygrams


class Data:
    def __init__(self, files):
        self.load_files(files)

        set1 = set(self.left_alignments)
        set2 = set(self.right_alignments)

        self.left_pool = list(set1.intersection(set1.difference(set2)))
        self.right_pool = list(set2.intersection(set2.difference(set1)))

        self.gold = list(set1.intersection(set2))

        self.left_stats = [len(self.left_alignments), len(self.left_alignments) + len(self.left_pool)]
        self.right_stats = [len(self.right_alignments), len(self.right_alignments) + len(self.right_pool)]

    def load_files(self, files):
        self.left_label = os.path.basename(files[0]).upper()
        self.right_label = os.path.basename(files[1]).upper()
        file1 = open(files[0], 'r', encoding='utf-8')
        file2 = open(files[1], 'r', encoding='utf-8')
        alignments1 = file1.read()
        alignments2 = file2.read()
        file1.close()
        file2.close()
        # each alignment should be 2 lines
        self.left_alignments = alignments1.split('\n\n')
        self.right_alignments = alignments2.split('\n\n')

    def find_candidate(self, target):
        """
        Find the most likely alignment based on ngrams
        """
        best = None
        best_overlap = 0
        for alignment in self.right_pool:
            overlap = []
            for line in target.split('\n'):
                if line in alignment:
                    overlap.append(line)
            if len(overlap) > best_overlap:
                best_overlap = len(overlap)
                best = alignment
        for alignment in self.right_pool:
            overlap = []
            for line in alignment.split('\n'):
                if line in target:
                    overlap.append(line)
            if len(overlap) > best_overlap:
                best_overlap = len(overlap)
                best = alignment
        if best is None:
            print('Resulting to ngrams.')
            target_grams = list(everygrams(target.replace('\n', '').split(), max_len=2))

            for alignment in self.right_pool:
                candidate_grams = list(everygrams(alignment.replace('\n', '').split(), max_len=2))
                overlap = []  # we don't want uniq so a set won't do
                for gram in target_grams:
                    if gram in candidate_grams:
                        overlap.append(gram)
                # make sure the overlap is at least 50% of the length of whichever gram list is longer
                if len(overlap) > best_overlap and len(overlap) * 2.0 > max(len(target_grams), len(candidate_grams)):
                    best_overlap = len(overlap)
                    best = alignment
        return best

    def select_option(self, correct, wrong):
        self.gold.append(correct)
        if correct in self.right_pool:
            self.right_pool.remove(correct)
            self.left_pool.remove(wrong)
            self.right_stats[1] -=1
        elif correct in self.left_pool:
            self.left_pool.remove(correct)
            self.right_pool.remove(wrong)
            self.left_stats[1] -= 1

    def both_wrong(self, left, right):
        self.left_pool.remove(left)
        self.right_pool.remove(right)

    def stats_str(self):
        left_score = self.left_stats[0] / self.left_stats[1] * 100.0
        right_score = self.right_stats[0] / self.right_stats[1] * 100.0
        remaining = min(len(self.left_pool), len(self.right_pool))
        return f'{self.left_label}: {left_score:.2f}. {self.right_label}: {right_score:.2f}. REMAINING: {remaining}'


def main(opts):
    data = Data(opts.files)

    while len(data.left_pool):
        left = data.left_pool[0]
        right = data.find_candidate(left)
        if right is None:
            print(f'Could not find a candidate for "{left[0:40]}". Skipping...')
            data.left_pool.remove(left)
        else:
            print(data.stats_str())
            print("\n", left, "\n---------\n", right)
            answer = input("\n1) Top. 2) Bottom. 3) Neither.")
            match answer:
                case '1':
                    data.select_option(left, right)
                case '2':
                    data.select_option(right, left)
                case _:
                    data.both_wrong(left, right)

    output = open('gold.txt', 'w', encoding='utf-8')
    for g in [g.strip() for g in data.gold if len(g.strip())]:
        output.write(g + "\n\n")
    output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', required=True, nargs='+', help='2 alignment files to compare')
    args = parser.parse_args()
    if len(args.files) != 2:
        parser.error('Must provide 2 alignment files')

    main(args)
