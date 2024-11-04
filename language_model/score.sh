#!/usr/bin/env bash
dir="$SUBTITLE_REPO/language_model/data"
source="eng"
target="spa"
pred_file="$dir/wmt13-en-es.pred"

# Download the test set if it doesn't already exist
if [ ! -s "wmt13-en-es.eng" ]; then
    sacrebleu -t wmt13 -l en-es --echo src > wmt13-en-es.src
fi

cat "wmt13-en-es.src" \
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

sacrebleu -t wmt13 -l en-es < "language_model/data/predictions-spa.txt"
