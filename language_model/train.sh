#!/usr/bin/env bash

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi

dir="$SUBTITLE_REPO/language_model/data"
# Train the model
fairseq-train \
    "$dir/preprocessed" \
    --source-lang="eng" \
    --target-lang="spa" \
    --arch transformer \
    --dropout 0.2 \
    --scoring sacrebleu \
    --max-tokens=8192 \
    --optimizer=adam
