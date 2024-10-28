#!/usr/bin/env bash

seed=1234
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi

dir="$SUBTITLE_REPO/language_model/data"
# Train the model
CUDA_VISIBLE_DEVICES=0 fairseq-train \
    "$dir/preprocessed" \
    --max-epoch=70 \
    --seed=1234 \
    --activation-fn="relu" \
    --source-lang="eng" \
    --target-lang="spa" \
    --arch transformer \
    --dropout=0.2 \
    --attention-dropout=0.2 \
    --lr=0.0005 \
    --encoder-layers=6 \
    --encoder-embed-dim=256 \
    --encoder-attention-heads=8 \
    --encoder-normalize-before \
    --encoder-ffn-embed-dim=1024 \
    --decoder-layers=6 \
    --decoder-embed-dim=256 \
    --decoder-attention-heads=8 \
    --decoder-normalize-before \
    --decoder-ffn-embed-dim=1024 \
    --share-decoder-input-output-embed \
    --lr-scheduler=inverse_sqrt \
    --warmup-updates=4000 \
    --warmup-init-lr='1e-07' \
    --label-smoothing=0.1 \
    --weight-decay=0.0001 \
    --criterion=label_smoothed_cross_entropy \
    --label-smoothing=0.1 \
    --optimizer=nag \
    --clip-norm=1.0 \
    --scoring=sacrebleu \
    --max-tokens=3000 \
    --max-update=400000 \
    --update-freq=8 \
    --patience=5 \
    --save-interval=1 \
    --no-epoch-checkpoints \
    || exit 1
