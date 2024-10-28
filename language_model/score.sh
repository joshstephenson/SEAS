#!/usr/bin/env bash

dir="$SUBTITLE_REPO/language_model/data"

fairseq-generate \
    "$dir/preprocessed" \
    --source-lang="eng" \
    --target-lang="spa" \
    --path="./checkpoints/checkpoint_best.pt" \
    --gen-subset="test" \
    --beam=5 \
    --batch-size=256 \
        > "$dir/predictions-spa.txt" \
        || exit 1
