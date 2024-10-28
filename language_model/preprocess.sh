#!/usr/bin/env bash

seed=1234

if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi
usage() {
    echo "Usage: $0 [alignments filename]"
    exit 1
}

if [ "$#" -lt 1 ] || [ ! -f "$1" ]; then
    usage
fi
filename="$1"
dir="$SUBTITLE_REPO/language_model/data"
source="eng"
target="spa"
source_file="$dir/all.$source"
target_file="$dir/all.$target"
if [ ! -d "$dir" ]; then
    mkdir "$dir"
    count=1
    echo "Extracting alignments..."
    # Alignments are in a single file in lines of 3. The first line is the source file
    # The second line is the target and the third is an empty line for separation.
    while read -r line; do
        if (( count % 3 == 1 )); then
            echo "$line" >> "$source_file"
        elif (( count % 3 == 2 )); then
            echo "$line" >> "$target_file"
        fi
        ((count++))
    done < "$filename"
fi

# Now generate the splits
if [ ! -s "$dir/train.$source" ]; then
    # Get the total number of lines
    total_lines=$(wc -l < "$source_file")

    # Calculate line counts for each split
    train_lines=$((total_lines * 80 / 100))
    val_lines=$((total_lines * 10 / 100))
    test_lines=$((total_lines - train_lines - val_lines))

    # Split the file
    head -n "$train_lines" "$source_file" > "$dir/train.$source"
    head -n "$train_lines" "$target_file" > "$dir/train.$target"

    tail -n +"$((train_lines + 1))" "$source_file" | head -n "$val_lines" > "$dir/valid.$source"
    tail -n +"$((train_lines + 1))" "$target_file" | head -n "$val_lines" > "$dir/valid.$target"

    tail -n "$test_lines" "$source_file" > "$dir/test.$source"
    tail -n "$test_lines" "$target_file" > "$dir/test.$target"
fi

# Now we can tokenize them
source_model_file="$dir/$source.model"
target_model_file="$dir/$target.model"
source_vocab_file="$dir/$source.vocab"
target_vocab_file="$dir/$target.vocab"
if [ ! -s "$source_model_file" ] || [ ! -s "$target_model_file" ]; then
    for set in $source $target; do
        echo "Training $set tokenizer..."
        "$SUBTITLE_REPO/spm/spm_train.py" \
            --input="$dir/all.$set" \
            --model-prefix="$dir/$set" \
            --vocab-size=16000 \
            || exit 1
        # Omitting special tokens <unk>, <s>, </s> replace all numbers in 2nd column with 100
        tail -n +4 "${dir}/${set}.vocab" | cut -f 1 | sed "s/$/ 100/g" > "${dir}/${set}.vocab.tmp"
        mv -f "${dir}/${set}.vocab.tmp" "${dir}/${set}.vocab"
    done
fi
echo -e "\nFinished training tokenizers: $source $target"

# Now tokenize the files with the tokenizer
mkdir -p "$dir/tokens"
for set in $source $target; do
    find "$dir" | grep -E ".+\.$set" | grep -v '.tok.' | grep -v 'all' | while read -r file; do
        line_count=$(wc -l < "$file" | tr -d ' ')
        base_file=$(basename "$file")
        tokens_file="$dir/tokens/${base_file//.$set/.tok.$set}"
        if [ ! -s "$tokens_file" ]; then
            echo "Encoding $file..."
            "$SUBTITLE_REPO/spm/spm_encode.py" \
            --model="${dir}/${set}.model" \
            --input="$file" \
            --output="$tokens_file" \
            --line-count="$line_count" \
                || exit 1
        fi
    done
done

# Fairseq preprocessing
echo "Preprocessing..."
mkdir -p "$dir/preprocessed"
count=$(ls "$dir/preprocessed" | wc -l)
if [ "$count" -lt 2 ]; then
    fairseq-preprocess \
        --source-lang "$source" \
        --target-lang "$target" \
        --srcdict="$source_vocab_file" \
        --tgtdict="$target_vocab_file" \
        --seed "$seed" \
        --thresholdsrc=1 \
        --thresholdtgt=1 \
        --trainpref="$dir/tokens/train.tok" \
        --validpref="$dir/tokens/valid.tok" \
        --testpref="$dir/tokens/test.tok" \
        --destdir="$dir/preprocessed" \
            || exit 1
fi
echo "Done preprocessing. Ready for training."
