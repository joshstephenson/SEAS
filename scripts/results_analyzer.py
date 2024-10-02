#!/usr/bin/env python

import argparse
import os
from math import ceil
import time
from nltk import everygrams
import curses

DELAY=0.20

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
            # print('Resulting to ngrams.')
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

    def stats(self):
        left_score = self.left_stats[0] / self.left_stats[1] * 100.0
        right_score = self.right_stats[0] / self.right_stats[1] * 100.0
        remaining = min(len(self.left_pool), len(self.right_pool))
        return f'{left_score:.2f}%', f'{right_score:.2f}%', f'GOLD: {len(self.gold)}\nREMAINING: {remaining}'


def main(opts):
    def draw_ui(stdscr, label1, label2):
        def set_bottom(text):
            bottom_pad.addstr(0, 0, text, curses.A_BOLD)
            bottom_pad.refresh(0, 0, 0, 0, 2, 30)

        def update_stats(stats):
            left_stats_len = len(stats[0])
            right_stats_len = len(stats[1])

            left_pad.addstr(1, 0, stats[0], curses.A_BOLD)
            left_pad.refresh(1, 0, 1, mid_width-left_stats_len-2, 1, content_width)
            right_pad.addstr(1, 0, stats[1], curses.A_BOLD)
            right_pad.refresh(1, 0, 1, mid_width, 1, full_width-1)

        def update_pads(left, right, standout=None):
            left_lines = left.split('\n')
            right_lines = right.split('\n')

            max_length = max(len(left_lines[0]), len(right_lines[0]))
            num_top_lines = ceil(max_length / content_width)
            num_bottom_lines = ceil(max(len(left_lines[1]), len(right_lines[1])) / content_width)

            # pad the lines so they line up vertically
            left_lines[0] = left_lines[0].ljust(num_top_lines * content_width, ' ')
            left_lines[1] = left_lines[1].ljust(num_bottom_lines * content_width, ' ')

            separator = '-' * (mid_width-2)
            left_str = f'{separator}'.join(left_lines)
            left_pad.addstr(3, 0, " " * 20 * content_width)
            if standout == 'left':
                left_pad.addstr(3, 0, left_str, curses.A_STANDOUT)
            else:
                left_pad.addstr(3, 0, left_str)
            left_pad.refresh(3, 0, 3, 0, 20, content_width)

            right_lines[0] = right_lines[0].ljust(num_top_lines * content_width, ' ')
            right_lines[1] = right_lines[1].ljust(num_bottom_lines * content_width, ' ')
            right_str = f'{separator}'.join(right_lines)
            right_pad.addstr(3, 0, " " * 20 * content_width)
            if standout == 'right':
                right_pad.addstr(3, 0, right_str, curses.A_STANDOUT)
            else:
                right_pad.addstr(3, 0, right_str)
            right_pad.refresh(3, 0, 3, mid_width, 20, full_width - 1)

        k = 0
        # Clear and refresh the screen for a blank canvas
        stdscr.clear()
        stdscr.refresh()
        # Initialization
        _, full_width = stdscr.getmaxyx()

        full_height = 40
        mid_width = int(full_width / 2.0)  # middle point of the window
        content_width = mid_width - 2

        left_pad = curses.newpad(full_height, content_width)
        right_pad = curses.newpad(full_height, content_width)
        # These labels won't change
        left_pad.addstr(0, 0, f'{label1}', curses.A_BOLD)
        right_pad.addstr(0, 0, f'{label2}', curses.A_BOLD)
        left_pad.refresh(0, 0, 0, content_width - len(label1), 1, mid_width)
        right_pad.refresh(0, 0, 0, mid_width, 1, full_width - 1)

        bottom_pad = curses.newpad(2, full_width - 1)

        while k != ord('q') and len(data.left_pool):
            left = data.left_pool[0]
            right = data.find_candidate(left)
            if right is None:
                # print(f'Could not find a candidate for "{left[0:40]}". Skipping...')
                data.left_pool.remove(left)
            else:
                stats = data.stats()
                update_stats(stats)
                update_pads(left, right)
                set_bottom(stats[2])
                # print("\n", left, "\n---------\n", right)
                k = stdscr.getch()
                match k:
                    case curses.KEY_LEFT:
                        update_pads(left, right, 'left')
                        time.sleep(DELAY)
                        data.select_option(left, right)
                    case curses.KEY_RIGHT:
                        update_pads(left, right, 'right')
                        time.sleep(DELAY)
                        data.select_option(right, left)
                    case curses.KEY_DOWN:
                        data.both_wrong(left, right)
                    case _:
                        pass

    data = Data(opts.files)
    if opts.annotate:
        curses.wrapper(draw_ui, data.left_label, data.right_label)

    output = open(opts.output, 'w', encoding='utf-8')
    gold = [g.strip() for g in data.gold if len(g.strip())]
    for g in gold:
        output.write(g + "\n\n")
    output.close()
    print(f'\n\nWrote {len(gold)} to {opts.output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', required=True, nargs='+', help='2 alignment files to compare')
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-a', '--annotate', action='store_true', default=False)
    args = parser.parse_args()
    if len(args.files) != 2:
        parser.error('Must provide 2 alignment files')

    main(args)
