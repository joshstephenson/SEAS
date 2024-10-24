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
base_dirname=$(dirname $(dirname "$source"))
source_lang=$(dirname "$source" | awk -F/ '{print $NF}')
target_lang=$(dirname "$target" | awk -F/ '{print $NF}')
# Check for suffixes from partitioning subtitles
suffix=''
if [[ "$source" =~ .+-[0-9]{3}.srt ]]; then
    suffix=-$(echo "$source" | awk -F/ '{print $NF}' | sed s/\.srt//g | cut -d- -f2)
fi
#echo "source: $source"
#echo "target: $target"
echo "Detecting $source_lang --> $target_lang in Dir: $base_dirname"

source_sent="${source/.srt/.sent}"
target_sent="${target/.srt/.sent}"
path_file="$base_dirname/${source_lang}-${target_lang}-vecalign${suffix}.path"
alignments_file="$base_dirname/${source_lang}-${target_lang}-vecalign${suffix}.txt"

if [ "$3" != "--skip-partitioning" ] && grep -E 'ShouldPartitionByGaps.+True' "$SUBTITLE_REPO/src/config.py" ; then
    echo "Extracting sentences directly and overlapping..."
    $SUBTITLE_REPO/scripts/srt2overlap.py -s "$source" -t "$target" -i

    echo "Embedding..."
    $SUBTITLE_REPO/scripts/sent2path.sh "$source_sent" "$target_sent" --skip-to-embed | grep -v "| INFO |" > "$path_file" #2>/dev/null
else
    echo "Extracting source sentences..."
    "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$source" -i -l "$source_lang" #2>/dev/null
    if [ ! -s "$source_sent" ]; then
        echo "Error creating source sentence file."
        exit 1
    fi
    echo "$source_sent"

    echo "Extracting target sentences..."
    "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$target" -i -l "$target_lang" #2>/dev/null
    if [ ! -s "$target_sent" ]; then
        echo "Error creating target sentence file."
        exit 1
    fi
    echo "$target_sent"

    echo "Overlapping and embedding..."
    "$SUBTITLE_REPO/scripts/sent2path.sh" "$source_sent" "$target_sent" | grep -v "| INFO |" > "$path_file" #2>/dev/null
    if [ ! -s "$path_file" ]; then
        echo "Error creating path file."
        exit 1
    fi
fi

if [ -z "$LASER" ]; then
    echo "Please set LASER env var to LASER repository."
    exit 1
fi

$SUBTITLE_REPO/scripts/path2align.py -s "$source_sent" -t "$target_sent" -a "$path_file" > "$alignments_file" #2>/dev/null
echo "$path_file"
echo "$alignments_file"
