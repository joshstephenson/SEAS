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
    cat "$dir/tokens/test.tok.$source" | head -n 1000 \
    | fairseq-interactive \
        "$dir/preprocessed" \
        --source-lang="$source" \
        --target-lang="$target" \
        --path="./checkpoints/checkpoint_best.pt" \
        --beam=5 \
        --batch-size=256 \
        --buffer-size=2000 \
    | grep '^H-' | cut -c 3- | awk -F '\t' '{print $NF}' \
    > "$pred_file" \
            || exit 1
fi

head -n 1000 "$dir/test.$source" > reference.$source
sacrebleu reference.$source -i "$pred_file" -m bleu

#grep '^H-' "$dir/predictions-spa.txt" | \
#    # strip the first 2 characters
#    cut -c 3- | \
#    # sort them numerically
#    sort -n -k 1 | \
#    # print only the last field
#    awk -F '\t' '{print $NF}' | \
#    # Remove whitespace and then replace underscores with whitespace (order here matters)
#    sed -e 's/[[:space:]]*//g' -e 's/[▁_]/ /g' | \
#    # Strip leading whitespace from the tokenization above and redirect to prediction file
#    sed -e 's/^ //g' #> "${PRED_FILE}"
