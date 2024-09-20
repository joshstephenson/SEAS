#!/usr/bin/env bash

FINDPATH=$1

if [ ! -d "$FINDPATH" ]; then
    echo "You must provide the path to the directory of one of the years of films."
    exit 1
fi

has_language_support() {
    DIR="$1"; shift
    LANGS="$@"
    for LANG in $LANGS; do
        if [ ! -d "$DIR/$LANG" ]; then
#            echo "Doesn't have $LANG"
            return 1
        fi
    done
    return 0
}

first_srt_for() {
    DIR="$1"
    LANG="$2"
    echo $(find "$DIR/$LANG/" -iname "*.srt" | head -n 1)
}

all_srt_for() {
    DIR="$1"
    LANG="$2"
    echo $(find "$DIR/$LANG/" -iname "*.srt")
}

TEMPFILE=/tmp/corpus_counter.tmp
STDERRFILE=/tmp/corpus_generator.err
echo 0 > $TEMPFILE
find "$FINDPATH" -d 1 -type d | while read -r DIR; do
    TITLE=$(head -n1 "$DIR/info.txt" | sed 's/^TITLE: //')
#    echo "Looking for language support for film: $TITLE"

    if has_language_support "$DIR" eng spa; then
        COUNT=1
        GENERATED=()
        for ENG_FILE in $(all_srt_for "$DIR" "eng"); do
            for SPA_FILE in $(all_srt_for "$DIR" "spa"); do
                OUT_FILE="$DIR/eng_spa-$COUNT.txt"

                # Run the alignment script
                if ./align.py \
                    -s "$ENG_FILE" \
                    -t "$SPA_FILE" 2> "$STDERRFILE" > "$OUT_FILE" ; then
                    GENERATED+=("$OUT_FILE")
                    COUNT=$((COUNT+1))
                else
                    # If alignment fails, remove the output file
                    rm -f "$OUT_FILE"
                    if grep 'No module named' "$STDERRFILE"; then
                        echo "You need to activate the python environment"
                        exit 1
                    fi
                fi
            done
        done

        # Save the largest file
        if [ "${#GENERATED[@]}" -ne 0 ]; then
            LARGEST=$(ls -S "${GENERATED[@]}" | head -n 1)
            NEW="${LARGEST//-*.txt/.txt}"
            mv "$LARGEST" "$NEW"
            if [ -s "$NEW" ]; then
                for FILE in "${GENERATED[@]}"; do
                    if [ -f "$FILE" ]; then
                        rm -f "$FILE"
                    fi
                done
                SHORT_PATH="$(basename "$DIR")/$(basename "$NEW")"
                echo "Saved (1/${#GENERATED[@]}) to: $SHORT_PATH"
                TOTAL=$[$(cat $TEMPFILE) + 1]
                echo $TOTAL > $TEMPFILE
            fi
        fi
    fi
done

echo "Aligned $(cat $TEMPFILE) Movies in eng -> spa"