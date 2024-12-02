#!/usr/bin/env bash

usage() {
    echo "Usage: $0 [alignments file] [dir to put alignment splits]"
    exit 1
}

if [ "$#" -lt 2 ] || [ ! -f "$1" ] || [ ! -d "$2" ]; then
    usage
fi
SOURCE='eng'
TARGET='spa'

filename="$1"
in_dir="$2"

source_file="$in_dir/all.$SOURCE"
target_file="$in_dir/all.$TARGET"
echo "$source_file"
if [ ! -s "$source_file" ]; then
    count=1
    echo "Extracting alignments..."
    # Alignments are in a single file in lines of 3. The first line is the SOURCE file
    # The second line is the TARGET and the third is an empty line for separation.
    while read -r line; do
        if (( count % 3 == 1 )); then
            echo "$line" >> "$source_file"
        elif (( count % 3 == 2 )); then
            echo "$line" >> "$target_file"
        fi
        ((count++))
    done < "$filename"
fi
