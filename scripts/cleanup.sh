#!/usr/bin/env bash

# GLOBAL VARS ARE HERE
source ~/.opensubtitles_project

DATA_DIR="$SUBTITLE_DATA/processed"

if [ -z "$1" ]; then
    read -p "Would you like to clean all directories under $DATA_DIR? (Yn)" CONFIRM
    if [ "$CONFIRM" == 'y' ]; then
        SEARCH_PATH="$DATA_DIR"
    fi
else
    SEARCH_PATH="$1"
    if [ ! -d "$SEARCH_PATH" ]; then
        echo "PATH is not a valid directory."
        exit 1
    fi
fi

# Make sure not to match info.txt files
FILES=$(find -E "$SEARCH_PATH" -type f \! -regex '.*\.srt$' \! -iname "info.txt")
COUNT=$(echo "$FILES" | wc -l)
read -n1 -p  "Found $COUNT files to remove. Remove them now?"  CONFIRM
if [ "$CONFIRM" == 'y' ]; then
    for FILE in $FILES; do
        rm -f "$FILE" && echo "Removed $FILE"
    done
fi

