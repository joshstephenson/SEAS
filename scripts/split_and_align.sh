#!/usr/bin/env bash
#
# First splits SRT files into groups based on significant gaps in the timecodes
# Based on those gaps in the source file, it finds corresponding groups in target SRT file
# Files are saved with original file names with an infix '-NUM' where NUM is a 3 digit number
#
# After that, this file runs both timecode basad alignments and vector embedding alignments and then uses
# results_analyzer.sh to find overlap.
#
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] ; then
    echo "Usage: $0 [title dir] [source lang code] [target lang code] [split gap length]"
    exit 0
fi

BASE_DIR="$1"
SOURCE_LANG="$2"
TARGET_LANG="$3"
SPLIT_GAP_LENGTH="$4"

# Find subtitle files
# Subtile files are 8 or more digits with an .srt extension
SOURCE=$(find -E "$BASE_DIR/$SOURCE_LANG" -iregex ".+[0-9]{8,}.srt" -exec ls -S {} \; | tail -n 1)
TARGET=$(find -E "$BASE_DIR/$TARGET_LANG" -iregex ".+[0-9]{8,}.srt" -exec ls -S {} \; | tail -n 1)
echo "SOURCE: $SOURCE"
echo "TARGET: $TARGET"

# Remove old splits
yes | $SUBTITLE_REPO/scripts/cleanup.sh "$BASE_DIR"

# Now split them
$SUBTITLE_REPO/scripts/split_srt.py -s "$SOURCE" -t "$TARGET" -g "$SPLIT_GAP_LENGTH"

SOURCE_FILES=$(find -E "$BASE_DIR/$SOURCE_LANG" -iregex '.+-[0-9]{3}.srt' | sort)

# First do the align script for timecode-based alignments
# We don't split the files for this
TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode.txt"
$SUBTITLE_REPO/scripts/timecode_align.py -s "$SOURCE" -t "$TARGET" > "$TIME_FILE"

for SOURCE in ${SOURCE_FILES[@]}; do
    INFIX=$(echo $SOURCE | cut -d- -f2 | cut -d. -f1)
    TARGET="$(find -E "$BASE_DIR/$TARGET_LANG" -iregex ".+[0-9]{8,}-$INFIX.srt" -exec ls -S {} \; | tail -n 1)"
    SOURCE_SENT="${SOURCE/.srt/.sent}"
    TARGET_SENT="${TARGET/.srt/.sent}"
#    TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode-${INFIX}.txt"
    VEC_ALIGN_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec-${INFIX}.path"
    VEC_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vec-${INFIX}.txt"
#    echo "$SOURCE"
#    echo "$TARGET"
#    echo "$SOURCE_SENT"
#    echo "$TARGET_SENT"
#    echo "$TIME_FILE"
#    echo "$VEC_ALIGN_FILE"
#    echo "$VEC_FILE"
    echo ""

    if [ ! -s "$SOURCE_SENT" ]; then
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$SOURCE" > "$SOURCE_SENT"
    fi
    echo "$SOURCE_SENT"
    if [ ! -s "$TARGET_SENT" ]; then
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$TARGET" > "$TARGET_SENT"
    fi

    # Skip this Split because it doesn't have any subtitles to align
    if [ ! -s "$SOURCE_SENT" ] || [ ! -s "$TARGET_SENT" ]; then
        echo "SKIPPING ${INFIX}" >&2
        continue
    fi
    echo "SPLIT: $INFIX"

    echo "$TARGET_SENT"
    if [ ! -s "$VEC_ALIGN_FILE" ]; then
        "$SUBTITLE_REPO/scripts/sent2path.sh" "$SOURCE_SENT" "$TARGET_SENT" | grep -v "| INFO |" > "$VEC_ALIGN_FILE" #2>/dev/null
    fi
    echo "$VEC_ALIGN_FILE"
    if [ ! -s "$VEC_FILE" ]; then
        "$SUBTITLE_REPO/scripts/path2align.py" -s "$SOURCE_SENT" -t "$TARGET_SENT" -a "$VEC_ALIGN_FILE" > "$VEC_FILE"
    fi
done

VEC_FILE="$BASE_DIR/$SOURCE_LANG-$TARGET_LANG-vec.txt"
GOLD_FILE="$BASE_DIR/$SOURCE_LANG-$TARGET_LANG-gold.txt"

# Combine the vector alignments
cat "$BASE_DIR/$SOURCE_LANG-$TARGET_LANG"-vec-*.txt > "$VEC_FILE"

"$SUBTITLE_REPO/scripts/results_analyzer.py" -f "$TIME_FILE" "$VEC_FILE" -o "$GOLD_FILE" -a


