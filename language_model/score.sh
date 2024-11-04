#!/usr/bin/env bash
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set the SUBTITLE_REPO environment."
    exit 1
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 [sacrebleu test set]. Options are:"
    sacrebleu --list -l en-es
    exit 1
fi
sacreset="$1"
dir="$SUBTITLE_REPO/language_model/data"
source="eng"
target="spa"
source_file="$dir/$sacreset-en-es.src"
source_tok_file="$dir/$sacreset-en-es.tok.src"
pred_file="$dir/$sacreset-en-es.pred"

# Download the test set if it doesn't already exist
if [ ! -s "$source_tok_file" ]; then
    sacrebleu -t "$sacreset" -l en-es --echo src > "$source_file"
    # Now tokenize the input
    echo "Tokenizing $sacreset..."
    lines=$(wc -l < "$source_file" | tr -d ' ')
    "$SUBTITLE_REPO/spm/spm_encode.py" \
                --model="${dir}/eng.model" \
                --input="$source_file" \
                --output="$source_tok_file" \
                --line-count="$lines" \
                    || exit 1
fi

echo "Generating translations for $sacreset..."
cat "$source_tok_file" \
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
| sacrebleu -t "$sacreset" -l en-es
