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
$SUBTITLE_REPO/scripts/cleanup.sh "$BASE_DIR"

# Now split them
$SUBTITLE_REPO/scripts/split_srt.py -s "$SOURCE" -t "$TARGET" -g "$SPLIT_GAP_LENGTH"

SOURCE_FILES=$(find -E "$BASE_DIR/$SOURCE_LANG" -iregex '.+-[0-9]{3}.srt' | sort)

# First do the align script for timecode-based alignments
# We don't split the files for this
TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode.txt"
$SUBTITLE_REPO/scripts/run_chronos.py -s "$SOURCE" -t "$TARGET" > "$TIME_FILE"

for SOURCE in ${SOURCE_FILES[@]}; do
    INFIX=$(echo $SOURCE | cut -d- -f2 | cut -d. -f1)
    TARGET="$(find -E "$BASE_DIR/$TARGET_LANG" -iregex ".+[0-9]{8,}-$INFIX.srt" -exec ls -S {} \; | tail -n 1)"
    SOURCE_SENT="${SOURCE/.srt/.sent}"
    TARGET_SENT="${TARGET/.srt/.sent}"
#    TIME_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-timecode-${INFIX}.txt"
    PATH_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vecalign-${INFIX}.path"
    ALIGNMENTS_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-vecalign-${INFIX}.txt"
#    echo "$SOURCE"
#    echo "$TARGET"
#    echo "$SOURCE_SENT"
#    echo "$TARGET_SENT"
#    echo "$TIME_FILE"
#    echo "$PATH_FILE"
#    echo "$ALIGNMENTS_FILE"

    # Skip this Split because it doesn't have any subtitles to align
    if [ ! -s "$SOURCE" ] || [ ! -s "$TARGET" ]; then
        echo "SKIPPING ${INFIX}" >&2
        continue
    else
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$SOURCE" -l "$SOURCE_LANG" > "$SOURCE_SENT"
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$TARGET" -l "$TARGET_LANG" > "$TARGET_SENT"
        # Even though the subtitle file wasn't empty, the sent file still can be if everything was scrubbed in preprocessing
        if [ ! -s "$SOURCE_SENT" ] || [ ! -s "$TARGET_SENT" ]; then
            echo "SKIPPING ${INFIX} after sentence generation." >&2
            continue
        fi
    fi
    echo "SPLIT: $INFIX"

    echo "$TARGET_SENT"
    if [ ! -s "$PATH_FILE" ]; then
        if ! "$SUBTITLE_REPO/scripts/sent2path.sh" "$SOURCE_SENT" "$TARGET_SENT" | grep -v "| INFO |" > "$PATH_FILE"; then
            echo "Failed to generated path file."
            exit 1
        fi
    fi
    echo "$PATH_FILE"
    if [ ! -s "$ALIGNMENTS_FILE" ]; then
        if ! "$SUBTITLE_REPO/scripts/path2align.py" -s "$SOURCE_SENT" -t "$TARGET_SENT" -a "$PATH_FILE" > "$ALIGNMENTS_FILE"; then
            echo "Failed to generate alignments f ile."
            exit 1
        fi
    fi
done
ALIGNMENTS_FILE="$BASE_DIR/$SOURCE_LANG-$TARGET_LANG-vecalign.txt"
GOLD_FILE="$BASE_DIR/$SOURCE_LANG-$TARGET_LANG-gold.txt"

# Combine the vector alignments
cat "$BASE_DIR/$SOURCE_LANG-$TARGET_LANG"-vecalign-*.txt > "$ALIGNMENTS_FILE"

#"$SUBTITLE_REPO/scripts/results_analyzer.py" -f "$TIME_FILE" "$ALIGNMENTS_FILE" -o "$GOLD_FILE" -a


