#!/usr/bin/env bash
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set the SUBTITLE_REPO environment."
    exit 1
fi

dir="$SUBTITLE_REPO/language_model/data"
source="eng"
target="spa"
source_file="wmt13-en-es.src"
pred_file="$dir/wmt13-en-es.pred"

# Download the test set if it doesn't already exist
if [ ! -s "wmt13-en-es.eng" ]; then
    sacrebleu -t wmt13 -l en-es --echo src > "$source_file"
fi

# Now tokenize the input
"$SUBTITLE_REPO/spm/spm_encode.py" \
            --model="${dir}/eng.model" \
            --input="$source_file" \
            --output="${source_file}.tok" \
            --line-count="$((wc -l < "$source_file"))" \
                || exit 1

cat "${source_file}.tok" \
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
