#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 [source] [target]"
fi

SOURCE="$1"
TARGET="$2"

SOURCE_SENT="${SOURCE/.srt/.sent}"
TARGET_SENT="${TARGET/.srt/.sent}"
BASE_DIR="$(dirname $(dirname $SOURCE))"
SOURCE_LANG="$(basename $(dirname $SOURCE))"
TARGET_LANG="$(basename $(dirname $TARGET))"
TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode.txt"
VEC_ALIGN_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec.align"
VEC_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec.txt"
GOLD_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}.gold"

# First do the align script for timecode-based alignments
if [ ! -f "$TIME_FILE" ]; then
    $SUBTITLE_REPO/scripts/align.py -s "$SOURCE" -t "$TARGET" > "$TIME_FILE"
fi
#
# That was fast, now do the embedding method
if [ ! -f "$SOURCE_SENT" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$SOURCE" > "$SOURCE_SENT"
fi
if [ ! -f "$TARGET_SENT" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$TARGET" > "$TARGET_SENT"
fi
if [ ! -f "$VEC_ALIGN_FILE" ]; then
    $SUBTITLE_REPO/scripts/sent2emb.sh "$SOURCE_SENT" "$TARGET_SENT" | grep -v "| INFO |" > "$VEC_ALIGN_FILE"
fi
if [ ! -f "$VEC_FILE" ]; then
    $SUBTITLE_REPO/scripts/emb2align.py -s "$SOURCE_SENT" -t "$TARGET_SENT" -a "$VEC_ALIGN_FILE" > "$VEC_FILE"
fi
$SUBTITLE_REPO/scripts/results_analyzer.py -f "$TIME_FILE" "$VEC_FILE" -o "$GOLD_FILE" -a


