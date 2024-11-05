#!/usr/bin/env bash
source "$(dirname $0)/base.sh"

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi

# Train the model
CUDA_VISIBLE_DEVICES=0 fairseq-train \
    "$DIR/preprocessed" \
    --save-dir="$SAVE_DIR" \
    --max-epoch="$MAX_EPOCHS" \
    --seed="$SEED" \
    --activation-fn="$ACTIVATION" \
    --source-lang="$SOURCE" \
    --target-lang="$TARGET" \
    --arch "$ARCHITECTURE" \
    --dropout="$DROPOUT" \
    --attention-dropout="$DROPOUT" \
    --lr="$LEARNING_RATE" \
    --encoder-layers="$LAYERS" \
    --encoder-embed-dim="$EMBED_DIM" \
    --encoder-attention-heads="$HEADS" \
    --encoder-ffn-embed-dim="$HIDDEN_DIM" \
    --decoder-layers="$LAYERS" \
    --decoder-embed-dim="$EMBED_DIM" \
    --decoder-attention-heads="$HEADS" \
    --decoder-ffn-embed-dim="$HIDDEN_DIM" \
    --warmup-updates="$WARMUP" \
    --warmup-init-lr="$INIT_LEARNING_RATE" \
    --weight-decay="$WEIGHT_DECAY" \
    --criterion="$CRITERION" \
    --label-smoothing="$LABEL_SMOOTHING" \
    --scoring="$SCORING" \
    --optimizer="$OPTIMIZER" \
    --clip-norm="$CLIP_NORM" \
    --max-tokens="$MAX_TOKENS" \
    --max-update="$MAX_UPDATES" \
    --update-freq="$UPDATE_FREQUENCY" \
    --patience="$PATIENCE" \
    --stop-min-lr="$STOP_MIN_LEARNING_RATE" \
    --save-interval="$SAVE_INTERVAL" \
    --share-decoder-input-output-embed \
    --lr-scheduler=inverse_sqrt \
    --eval-bleu \
    --eval-bleu-remove-bpe \
    --no-epoch-checkpoints \
    --encoder-normalize-before \
    --decoder-normalize-before \
    || exit 1
