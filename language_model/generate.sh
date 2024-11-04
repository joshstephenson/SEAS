#!/usr/bin/env bash

dir="$SUBTITLE_REPO/language_model/data"
source="eng"
target="spa"
pred_file="$dir/predictions-spa.txt"

if [ -s "$pred_file" ]; then
    echo "$pred_file exists."
    # shellcheck disable=SC2162
    read -p "Do you want to proceed? (y/n) " confirm
fi

if [ -z "$confirm" ] || [ "$confirm" == 'y' ]; then
    rm -f "$pred_file" 2>/dev/null
    cat "$dir/tokens/test.tok.$source" \
    | fairseq-interactive \
        "$dir/preprocessed" \
        --source-lang="$source" \
        --target-lang="$target" \
        --path="./checkpoints/checkpoint_best.pt" \
        --beam=5 \
        --batch-size=256 \
        --buffer-size=2000 \
        --remove-bpe=sentencepiece \
    | grep '^H-' | cut -c 3- | awk -F '\t' '{print $NF}' \
    > "$pred_file" \
            || exit 1
fi
