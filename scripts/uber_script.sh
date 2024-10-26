#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] ; then
    echo "Usage: $0 [title dir] [source lang code] [target lang code]"
    exit 0
fi

base_dir="$1"
source_lang="$2"
target_lang="$3"

# Cleanup
yes | $SUBTITLE_REPO/scripts/cleanup.sh "$base_dir"

# First we have to find subtitle files to use
source=$(find -E "$base_dir/$source_lang" -iregex ".+[0-9]{4,10}.srt" -exec ls -S {} \; | tail -n 1)
target=$(find -E "$base_dir/$target_lang" -iregex ".+[0-9]{4,10}.srt" -exec ls -S {} \; | tail -n 1)
echo "source: $source"
echo "target: $target"

source_sent="${source/.srt/.sent}"
target_sent="${target/.srt/.sent}"
time_file="$base_dir/${source_lang}-${target_lang}-chronos.txt"
path_file="$base_dir/${source_lang}-${target_lang}-vecalign.path"
alignments_file="$base_dir/${source_lang}-${target_lang}-vecalign.txt"
gold_file="$base_dir/${source_lang}-${target_lang}.gold"

# First do the align script for timecode-based alignments
if [ ! -s "$time_file" ]; then
    $SUBTITLE_REPO/scripts/run_chronos.py -s "$source" -t "$target" > "$time_file"
fi
#
# That was fast, now do the embedding method
if [ ! -s "$source_sent" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$source" -l "$source_lang" > "$source_sent"
fi
if [ ! -s "$target_sent" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$target" -l "$target_lang" > "$target_sent"
fi
if [ ! -s "$path_file" ]; then
    $SUBTITLE_REPO/scripts/sent2path.sh "$source_sent" "$target_sent" | grep -v "| INFO |" > "$path_file" #2>/dev/null
fi
echo "$path_file"
if [ ! -s "$alignments_file" ]; then
    $SUBTITLE_REPO/scripts/path2align.py -s "$source_sent" -t "$target_sent" -p "$path_file" > "$alignments_file"
fi
echo "$alignments_file"
#$SUBTITLE_REPO/scripts/results_analyzer.py -f "$time_file" "$alignments_file" -o "$gold_file" -a


