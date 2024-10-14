#!/usr/bin/env python
"""
Takes two separate alignments and finds where they agree. Alignment files have one sentence on one line, the aligned
sentence from target language on the next line and then each alignment (pair) is separated by a newline.
Assuming the -a parameter for annotation, it allows the user to decide which annotation is correct where the two did not
agree.
"""
import argparse
import os.path
import subprocess
import curses

from src.Alignments import Alignments
from src.annotation import Annotation
from src.film import Film

DEBUG_Y = 0
SUBTITLE_Y = 2


def main(opts, alignments):
    def draw_ui(stdscr, label1, label2):

        def show_annotation(annotation: Annotation):
            left_window.erase()
            right_window.erase()

            if annotation.source.has_subtitles():
                left_window.addstr(SUBTITLE_Y, 0, annotation.source.lines())
                if annotation.source.has_utterance():
                    previous_y = SUBTITLE_Y
                    for subtitle in annotation.source.subtitles:
                        left_window.addstr(DEBUG_Y, 0, annotation.source.utterance)
                        y_offset, x_offset, length = annotation.source.get_offsets_and_length(subtitle)
                        try:
                            length_of_third = len(annotation.source.lines().split('\n')[y_offset])
                            lengths = [length_of_third, length - length_of_third - 1]
                            if length > length_of_third:
                                for i in range(2):
                                    left_window.chgat(y_offset + previous_y + i, 0, lengths[i], curses.A_STANDOUT)
                            else:
                                left_window.chgat(y_offset + previous_y, x_offset, length, curses.A_STANDOUT)
                        except curses.error as _:
                            pass
                        previous_y += y_offset + SUBTITLE_Y

            if annotation.target.has_subtitles():
                right_window.addstr(SUBTITLE_Y, 0, annotation.target.lines())
                if annotation.target.has_utterance():
                    previous_y = SUBTITLE_Y
                    for subtitle in annotation.target.subtitles:
                        right_window.addstr(DEBUG_Y, 0, annotation.target.utterance)
                        y_offset, x_offset, length = annotation.target.get_offsets_and_length(subtitle)
                        try:
                            length_of_third = len(annotation.target.lines().split('\n')[y_offset])
                            lengths = [length_of_third, length - length_of_third - 1]
                            if length > length_of_third:
                                for i in range(2):
                                    right_window.chgat(y_offset + previous_y + i, 0, lengths[i], curses.A_STANDOUT)
                            else:
                                right_window.chgat(y_offset + previous_y, x_offset, length, curses.A_STANDOUT)
                        except curses.error as _:
                            pass
                        previous_y += y_offset + SUBTITLE_Y

            left_window.refresh()
            right_window.refresh()

        k = 0
        # Clear and refresh the screen for a blank canvas
        stdscr.clear()
        stdscr.refresh()
        # Initialization
        full_height, full_width = stdscr.getmaxyx()

        half_width = int(full_width / 2.0)  # middle point of the window
        content_width = half_width - 2

        left_window = curses.newwin(full_height - 20, half_width, 0, 0)
        right_window = curses.newwin(full_height - 20, half_width, 0, half_width + 1)
        while k != ord('q'):
            annotation = film.get_annotation()
            show_annotation(annotation)

            k = stdscr.getch()
            match k:
                case curses.KEY_DOWN:
                    film.next()
                case curses.KEY_UP:
                    film.previous()
                case _:
                    pass

    film = Film(opts.source, opts.target, alignments)
    curses.wrapper(draw_ui, film.source.label, film.target.label)

def run_vecalign(opts):
    subprocess.run(['./scripts/run_vecalign.sh', opts.source, opts.target])

def sent_files_for_srt(srt_file) -> (str, str):
    return srt_file.replace('.srt', '.sent'), srt_file.replace('.srt', '.sent-index')

def alignment_files(source, target) -> (str, str):
    """
    returns a path to the alignments
    and a path to the index file
    """
    source_lang = source.split('/')[-2]
    target_lang = target.split('/')[-2]
    base_dir = source.split("/" + source_lang)[0]
    return f'{base_dir}/{source_lang}-{target_lang}-vec.path', f'{base_dir}/{source_lang}-{target_lang}-vec.txt'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Source subtitle file.')
    parser.add_argument('-t', '--target', required=True, help='Target subtitle file.')
    args = parser.parse_args()

    source_sent, source_sent_index = sent_files_for_srt(args.source)
    target_sent, target_sent_index = sent_files_for_srt(args.target)
    if not os.path.exists(source_sent) or not os.path.exists(target_sent):
        run_vecalign(args)

    paths_file, alignments_file = alignment_files(args.source, args.target)
    if not os.path.exists(alignments_file):
        print("Failure running vecalign.")
        exit(1)
    alignments = Alignments(paths_file, source_sent, source_sent_index, target_sent, target_sent_index)
    main(args, alignments)
