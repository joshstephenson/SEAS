#!/usr/bin/env python
"""
Allows fixing a files timestamps to match the other
"""
import os
import subprocess
import sys

from regex import regex

from src.alignments import Alignments
from src.film import Film
from src.helpers import get_text
from src.subtitles import Subtitles

OFFSET_MIN = 2 * 1e6


def run_vecalign(opts):
    subprocess.check_output(['./scripts/run_vecalign.sh', opts.source, opts.target, '--skip-partitioning'])


def sent_files_for_srt(srt_file) -> (str, str):
    return srt_file.replace('.srt', '.sent'), srt_file.replace('.srt', '.sent-index')


def alignment_files(source, target) -> (str, str):
    """
    returns a path to the alignments
    and a path to the index file
    """
    # See if these files are splits
    match = regex.match(r'\d{4,10}(-\d{3}).srt$', source.split('/')[-1])
    suffix = ''
    if match is not None and len(match.groups()) > 0:
        suffix = match.group(1)
    source_lang = source.split('/')[-2]
    target_lang = target.split('/')[-2]
    base_dir = source.split("/" + source_lang)[0]
    return (f'{base_dir}/{source_lang}-{target_lang}-vecalign{suffix}.path',
            f'{base_dir}/{source_lang}-{target_lang}-vecalign{suffix}.txt')


def delay_and_save(filename, subs, offset):
    for sub in subs:
        sub.delay_timecodes(offset)
    with open(filename, 'w') as f:
        # Write the source subs
        for sub in subs:
            f.write(sub.lines + '\n\n')
    seconds = offset / 1e6
    sys.stderr.write(f'Subtitles adjusted by {seconds:.4f} seconds')


def fix_offset(opts, film, offset):
    source_text = get_text(opts.source)
    target_text = get_text(opts.target)

    # Create Subtitle objects from the file texts
    source_subs = Subtitles(source_text, is_source=True)
    target_subs = Subtitles(target_text, is_source=False)

    # We won't ever advance subtitles, only delay them
    if offset > 0:
        delay_and_save(opts.target, target_subs, offset)
    else:  # push source subtitles forward
        delay_and_save(opts.source, source_subs, offset)

def main(opts, film: Film):
    offset = film.calculated_offset()
    if offset > OFFSET_MIN:
        sys.stderr.write(f'Calculated offset of {offset} is greater than {OFFSET_MIN}.')
        fix_offset(opts, film, offset)
    else:
        sys.stderr.write(f'Calculated offset of {offset} is not greater than {OFFSET_MIN}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, help='Source subtitle file.')
    parser.add_argument('-t', '--target', required=True, help='Target subtitle file.')
    parser.add_argument('-i', '--ignore-empty', required=False, action='store_true',
                        help='Don\'t print subtitles with no valid content.')
    args = parser.parse_args()

    source_sent, source_sent_index = sent_files_for_srt(args.source)
    target_sent, target_sent_index = sent_files_for_srt(args.target)

    run_vecalign(args)

    paths_file, alignments_file = alignment_files(args.source, args.target)
    if not os.path.exists(alignments_file):
        print(f"Failure running vecalign.\nFile does not exist: {alignments_file}")
        exit(1)
    alignments = Alignments(paths_file, source_sent, source_sent_index, target_sent, target_sent_index)
    film = Film(args.source, args.target, alignments)
    main(args, film)