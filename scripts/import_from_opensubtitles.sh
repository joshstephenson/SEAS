#!/usr/bin/env bash

EXPORT_FILE="export.txt"
YEAR="$1"
EMPTY_MOVIE="Empty Movie"

if [ -z "$YEAR" ]; then
    echo "Must pass year."
    exit 1
fi
if [ -z "$EXTRACT_SCRIPT" ]; then
    echo "Set EXTRACT_SCRIPT env variable to location of sentence extractor script."
    exit 1
fi
if [ -z "$SUBTITLE_DATA" ]; then
    echo "Set SUBTITLE_DATA env variable to the location of the OpenSubtitle Data. No trailing slash."
fi

EXPORT_FILE="$SUBTITLE_DATA/$EXPORT_FILE"
find_by_year() {
    years=$(awk -F'\t' '{print $9}' $EXPORT_FILE | grep -v MovieYear | sort -r | uniq | head -n20)

    for year in $years; do
        awk -F'\t' -v year="$year" '$9 == year' $EXPORT_FILE | grep -v 'Empty Movie' > "$SUBTITLE_DATA/processed/$year.txt"
    done
}

get_year() {
    LINE="$1"
    echo "$LINE" | awk -F'\t' '{print $9}'
}

get_lang() {
    LINE="$1"
    echo "$LINE" | awk -F'\t' '{print $3}'
}

get_title() {
    LINE="$1"
    echo "$LINE" | awk -F'\t' '{print $8}'
}

srt_file() {
    LINE="$1"
    ID=$(echo "$LINE" | awk -F'\t' '{print $2}')
    echo -n "$SUBTITLE_DATA/files/"
    for i in $(seq 4); do
        echo "$ID" | tail -c $((1+i)) | head -c 1
        echo -n "/"
    done
    echo "$ID.gz"
}

is_movie() {
    LINE="$1"
    SEASON=$(echo "$LINE" | awk -F'\t' '{print $14}')
    EPISODE=$(echo "$LINE" | awk -F'\t' '{print $15}')
    if [ -n "$SEASON" ] && [ -n "$EPISODE" ] && [ "$SEASON" -eq 0 ] && [ "$EPISODE" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

new_file() {
    LINE="$1"
    YEAR="$(get_year "$LINE")"
    CLEANED="$(get_title "$LINE" | sed 's/ /_/g' | sed 's/[^a-zA-Z0-9_-]//g' | tr -s "_")"
    LANG="$(get_lang "$LINE")"
    FILE="$(echo "$LINE" | awk -F'\t' '{print $2}')"
    echo "$SUBTITLE_DATA/processed/$YEAR/$CLEANED/$LANG/$FILE.srt.gz"
}

process_file() {
    LINE="$1"
    TITLE="$(get_title "$LINE")"
    CLEANED="$(get_title "$LINE" | sed 's/ /_/g' | sed 's/[^a-zA-Z0-9_-]//g' | tr -s "_")"
    ID=$(echo "$LINE" | awk -F'\t' '{print $2}')
    OLD="$(srt_file "$LINE")"
    NEW="$(new_file "$LINE")"
    mkdir -p $(dirname "$NEW")
    cp "$OLD" "$NEW"
    INFO_FILE="$SUBTITLE_DATA/processed/$YEAR/$CLEANED/info.txt"
    echo "TITLE: $TITLE" > "$INFO_FILE"
    echo "YEAR: $YEAR" >> "$INFO_FILE"
    echo "ID: $ID" >> "$INFO_FILE"
    if is_movie "$LINE"; then
        echo "TYPE: FILM" >> "$INFO_FILE"
    else
        SEASON=$(echo "$LINE" | awk -F'\t' '{print $14}')
        EPISODE=$(echo "$LINE" | awk -F'\t' '{print $15}')
        printf "TYPE: SERIES\nSEASON: $SEASON\nEPISODE: $EPISODE\n" >> "$INFO_FILE"
    fi
    gunzip "$NEW"
    # Remove the .gz file if it hangs around
    rm -f "$NEW"
}

process_year() {
    while IFS= read -r LINE; do
        TITLE="$(get_title "$LINE")"
        CLEANED="$(get_title "$LINE" | sed 's/ /_/g' | sed 's/[^a-zA-Z0-9_-]//g' | tr -s "_")"
        if [[ "$TITLE" == *"$EMPTY_MOVIE"* ]]; then
            echo "SKIPPING EMPTY MOVIE: $TITLE"
        elif [ -z "$CLEANED" ]; then
            echo "SKIPPING (No Title)"
        else
            echo "PROCESSING: $TITLE"
            process_file "$LINE"
        fi
    done < "$SUBTITLE_DATA/index/$YEAR.txt"
}
#find_by_year
process_year


#LINE=$(head -n10 "$EXPORT_FILE" | tail -n1)
#
#FILENAME=$(srt_file "$LINE")
#ls -alh "$FILENAME"
