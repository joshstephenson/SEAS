#!/usr/bin/env bash

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 [directory] [lang] [limit]"
    exit 1
fi
DIR="$1"
LANG="$2"
LIMIT="$3"

SENT_FILE="$DIR/$LANG.sent"
OVERLAP_FILE="$DIR/$LANG.overlaps"
EMB_FILE="$DIR/$LANG.emb"
LINE_COUNT=0
rm -f "$SENT_FILE"
rm -f "$OVERLAP_FILE"
rm -f "$EMB_FILE"
find "$DIR" -ipath "*/$LANG/*.sent" | while read -r FILE; do
    cat "$FILE" >> "$SENT_FILE"
    LINES=$(wc -l < "$FILE")
    LINE_COUNT=$(($LINE_COUNT + LINES))
    if [[ $LINE_COUNT -gt $((LIMIT)) ]]; then
        echo "Reached limit of $LIMIT"
        break
    fi
done
echo "Concatenated LINE_COUNT to $SENT_FILE"

./vecalign/overlap.py -n 5 -i "$SENT_FILE" -o "$OVERLAP_FILE"
echo "Generated overlaps of 5 to $OVERLAP_FILE"
./LASER/tasks/embed/embed.sh "$OVERLAP_FILE" "$EMB_FILE"
