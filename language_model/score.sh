#!/usr/bin/env bash
source "$(dirname $0)/base.sh"

if [ $# -lt 1 ]; then
    echo "Usage: $0 [sacrebleu test set]. Options are:"
    sacrebleu --list -l en-es
    exit 1
fi
sacreset_ref="$1"
sacreset=$(echo "$sacreset_ref" | tr '/' '_')
mkdir -p "$DIR/sacrebleu"
source_file="$DIR/sacrebleu/$sacreset-en-es.src"
source_tok_file="$DIR/sacrebleu/$sacreset-en-es.tok.src"
pred_file="$DIR/sacrebleu/$sacreset-en-es.pred"

# Download the test set if it doesn't already exist
if [ ! -s "$source_tok_file" ]; then
    sacrebleu -t "$sacreset_ref" -l en-es --echo src > "$source_file"
    # Now tokenize the input
    echo "Tokenizing $sacreset..."
    lines=$(wc -l < "$source_file" | tr -d ' ')
    "$SUBTITLE_REPO/spm/spm_encode.py" \
                --model="$DIR/eng.model" \
                --input="$source_file" \
                --output="$source_tok_file" \
                --line-count="$lines" \
                    || exit 1
fi

echo "Generating translations for $sacreset..."
cat "$source_tok_file" \
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
> "$pred_file" \
    || exit 1
cat "$pred_file" | sacrebleu -t "$sacreset_ref" -l en-es -m bleu chrf ter > "$DIR/sacrebleu.results.txt"
cat "$DIR/sacrebleu.results.txt"
