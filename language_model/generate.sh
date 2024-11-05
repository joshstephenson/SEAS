#!/usr/bin/env bash
source "$(dirname $0)/base.sh"

if [ -s "$PRED_FILE" ]; then
    echo "$PRED_FILE exists."
    # shellcheck disable=SC2162
    read -p "Do you want to proceed? (y/n) " confirm
fi

if [ -z "$confirm" ] || [ "$confirm" == 'y' ]; then
    rm -f "$PRED_FILE" 2>/dev/null
    cat "$TOKENS_DIR/test.tok.$SOURCE" \
    | fairseq-interactive \
        "$PREPROCESSED_DIR" \
        --source-lang="$SOURCE" \
        --target-lang="$TARGET" \
        --path="$SAVE_DIR/checkpoint_best.pt" \
        --beam="$BEAM" \
        --batch-size="$BATCH_SIZE" \
        --buffer-size="$BUFFER_SIZE" \
        --remove-bpe=sentencepiece \
    | grep '^H-' | cut -c 3- | awk -F '\t' '{print $NF}' \
    > "$PRED_FILE" \
            || exit 1
fi
