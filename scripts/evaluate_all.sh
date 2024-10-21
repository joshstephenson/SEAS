#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO env to root of this repo"
    exit 1
fi


usage() {
    echo "Usage: $0 [source lang code] [target lang code]"
    exit 1
}

print_config() {
    lines=$(tail -n+2 "$SUBTITLE_REPO/src/config.py" | wc -l)  # Get the total number of lines

    while IFS= read -r line; do
        # Strip leading/trailing whitespace, replace ' = ' with ': ', and add comma only if not the last line

        cleaned=$(echo -n "$line" | sed -e 's/^ *//; s/ *$//')
        label=$(echo "$cleaned" | cut -d= -f1)
        value=$(echo "$cleaned" | cut -d= -f2)
        printf "%-22s %-10s\n" "$label" "$value"
    done < <(tail -n+2 "$SUBTITLE_REPO/src/config.py")
    echo ""
}

ellipsize() {
    max_length=15

    if [ ${#1} -gt $max_length ]; then
        front="${1:0:7}"    # First 7 characters
        end="${1: -5}"      # Last 5 characters
        ellipsized="${front}...${end}"  # Combine with ellipsis in the middle
    else
        ellipsized="$1"     # No need to ellipsize if within the limit
    fi

    echo "$ellipsized"
}

if [ "$#" -ne 2 ]; then
    usage
fi

print_config

source="$1"
target="$2"

total_tp=0
total_fn=0
total_fp=0
count=0

printf "%-15s  %-15s  %-15s  %-15s  %-10s %-10s %-10s\n" "Title" "True Positives" "False Negatives" "False Positives" "Recall" "Precision" "F-1"
for dir in "$SUBTITLE_REPO/gold/"*; do
    "$SUBTITLE_REPO/scripts/run_and_eval.sh" vecalign "$dir" "$source" "$target" 2>$1 >/dev/null
    results=$( tail -n1 "$dir/$source-$target-vecalign.results")
    title=$(ellipsize "$(basename "$dir")")
    recall=$(echo "$results" | cut -f4)
    precision=$(echo "$results" | cut -f5)
    f1=$(echo "$results" | cut -f6)
    tp=$(echo "$results" | cut -f1)
    fn=$(echo "$results" | cut -f2)
    fp=$(echo "$results" | cut -f3)

    total_tp=$(echo "$total_tp" + "$tp" | bc)
    total_fn=$(echo "$total_fn" + "$fn" | bc)
    total_fp=$(echo "$total_fp" + "$fp" | bc)

    printf "%-15s  %-15d  %-15d  %-15d  %-0.6f   %-0.6f   %-0.6f\n" "$title" "$tp" "$fn" "$fp" "$recall" "$precision" "$f1"

    count=$((count + 1))
done

if [ $count -ne 0 ]; then
    recall=$(echo "scale=6; $total_tp / ($total_tp + $total_fn)" | bc)
    precision=$(echo "scale=6; $total_tp / ($total_tp + $total_fp)" | bc)
    f1=$(echo "scale=6; 2 * $recall * $precision / ($recall + $precision)" | bc)
    printf "                 %-15d  %-15d  %-15d  %-0.6f   %-0.6f   %-0.6f\n" "$total_tp" "$total_fn" "$total_fp" "$recall" "$precision" "$f1"
fi
echo ""