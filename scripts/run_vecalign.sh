#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ $# -lt 2 ]; then
    echo "Usage: $0 [source file] [target file]"
    exit 0
fi

source="$1"
target="$2"
base_dirname=$(dirname "$(dirname "$source")")
source_lang=$(dirname "$source" | awk -F/ '{print $NF}')
target_lang=$(dirname "$target" | awk -F/ '{print $NF}')

# Check for suffixes from partitioning subtitles
suffix=''
if [[ "$source" =~ .+-[0-9]{3}.srt ]]; then
    suffix=-$(echo "$source" | awk -F/ '{print $NF}' | sed s/\.srt//g | cut -d- -f2)
fi
echo "source: $source" >&2
echo "target: $target" >&2
echo "Detecting $source_lang --> $target_lang in Dir: $base_dirname" >&2

source_sent="${source/.srt/.sent}"
target_sent="${target/.srt/.sent}"
path_file="$base_dirname/${source_lang}-${target_lang}-vecalign${suffix}.path"
alignments_file="$base_dirname/${source_lang}-${target_lang}-vecalign${suffix}.txt"

if [ -z "$LASER" ]; then
    echo "Please set LASER env var to LASER repository."
    exit 1
fi

if [ "$3" != "--skip-partitioning" ] && grep -E 'ShouldPartitionByGaps.+True' "$SUBTITLE_REPO/src/config.py" ; then
    echo "Extracting sentences directly and overlapping..." >&2
    "$SUBTITLE_REPO/scripts/srt2overlap.py" -s "$source" -t "$target" -i

    echo "Embedding..." >&2
    "$SUBTITLE_REPO/scripts/sent2path.sh" "$source_sent" "$target_sent" --skip-to-embed | grep -v "| INFO |" > "$path_file" #2>/dev/null
else
    echo "Extracting source sentences..." >&2
    "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$source" -i -l "$source_lang" 2>/dev/null || exit 1
    if [ ! -s "$source_sent" ]; then
        echo "Error creating source sentence file for: $source"
        exit 1
    fi

    echo "Extracting target sentences..." >&2
    "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$target" -i -l "$target_lang" 2>/dev/null || exit 1
    if [ ! -s "$target_sent" ]; then
        echo "Error creating target sentence file for: $target"
        exit 1
    fi

    echo "Overlapping and embedding..." >&2
    "$SUBTITLE_REPO/scripts/sent2path.sh" "$source_sent" "$target_sent" | grep -v "| INFO |" > "$path_file" 2>/dev/null || exit 1
    if [ ! -s "$path_file" ]; then
        echo "Error creating path file."
        exit 1
    fi
fi

"$SUBTITLE_REPO/scripts/path2align.py" -s "$source_sent" -t "$target_sent" -p "$path_file" > "$alignments_file" 2>/dev/null
echo "$path_file" >&2
echo "$alignments_file" >&2
