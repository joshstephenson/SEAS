#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] ; then
    echo "Usage: $0 [title dir] [source lang code] [target lang code]"
    exit 0
fi

BASE_DIR="$1"
SOURCE_LANG="$2"
TARGET_LANG="$3"

# First we have to find subtitle files to use
SOURCE=$(find "$BASE_DIR/$SOURCE_LANG" -iname "*.srt" -exec ls -S {} \; | tail -n 1)
TARGET=$(find "$BASE_DIR/$TARGET_LANG" -iname "*.srt" -exec ls -S {} \; | tail -n 1)
echo "SOURCE: $SOURCE"
echo "TARGET: $TARGET"

SOURCE_SENT="${SOURCE/.srt/.sent}"
TARGET_SENT="${TARGET/.srt/.sent}"
TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode.txt"
VEC_ALIGN_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec.path"
VEC_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec.txt"
GOLD_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}.gold"

# First do the align script for timecode-based alignments
if [ ! -f "$TIME_FILE" ]; then
    $SUBTITLE_REPO/scripts/timecode_align.py -s "$SOURCE" -t "$TARGET" > "$TIME_FILE"
fi
echo "$TIME_FILE"
#
# That was fast, now do the embedding method
if [ ! -f "$SOURCE_SENT" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$SOURCE" > "$SOURCE_SENT"
fi
echo "$SOURCE_SENT"
if [ ! -f "$TARGET_SENT" ]; then
    $SUBTITLE_REPO/scripts/srt2sent.py -f "$TARGET" > "$TARGET_SENT"
fi
echo "$TARGET_SENT"
if [ ! -f "$VEC_ALIGN_FILE" ]; then
    $SUBTITLE_REPO/scripts/sent2emb.sh "$SOURCE_SENT" "$TARGET_SENT" | grep -v "| INFO |" > "$VEC_ALIGN_FILE" #2>/dev/null
fi
echo "$VEC_ALIGN_FILE"
if [ ! -f "$VEC_FILE" ]; then
    $SUBTITLE_REPO/scripts/emb2align.py -s "$SOURCE_SENT" -t "$TARGET_SENT" -a "$VEC_ALIGN_FILE" > "$VEC_FILE"
fi
echo "$VEC_FILE"
$SUBTITLE_REPO/scripts/results_analyzer.py -f "$TIME_FILE" "$VEC_FILE" -o "$GOLD_FILE" -a


