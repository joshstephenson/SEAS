#!/usr/bin/env bash

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
    echo "Training tokenizer..."
    "$SUBTITLE_REPO/spm/spm_train.py" \
        --input="$dir/all.$source" \
        --model-prefix="$dir/$source" \
        || exit 1
    # Omitting special tokens <unk>, <s>, </s> replace all numbers in 2nd column with 100
    tail -n +4 "$source_vocab_file" | cut -f 1 | sed "s/$/ 100/g" > "${source_vocab_file}.tmp"
    mv -f "${source_vocab_file}.tmp" "$source_vocab_file"

    "$SUBTITLE_REPO/spm/spm_train.py" \
        --input="$dir/all.$target" \
        --model-prefix="$dir/$target" \
        || exit 1
    # Omitting special tokens <unk>, <s>, </s> replace all numbers in 2nd column with 100
    tail -n +4 "$target_vocab_file" | cut -f 1 | sed "s/$/ 100/g" > "${target_vocab_file}.tmp"
    mv -f "${target_vocab_file}.tmp" "$target_vocab_file"
fi
echo ""
mkdir -p "$dir/tokens"
# Now tokenize the files with the tokenizer
find "$dir" | grep -E ".+\.$source" | grep -v 'tok' | grep -v 'all' | while read -r file; do
    line_count=$(wc -l < "$file" | tr -d ' ')
    base_file=$(basename "$file")
    tokens_file="$dir/tokens/${base_file//.$source/.tok.$source}"
    if [ ! -s "$tokens_file" ]; then
        echo "Encoding $file..."
        "$SUBTITLE_REPO/spm/spm_encode.py" \
        --model="$source_model_file" \
        --input="$file" \
        --output="$tokens_file" \
        --line-count="$line_count" \
            || exit 1
    fi
done

find "$dir" | grep -E ".+\.$target" | grep -v 'tok' | grep -v 'all' | while read -r file; do
    line_count=$(wc -l < "$file" | tr -d ' ')
    base_file=$(basename "$file")
    base="${base_file%.*}"
    tokens_file="$dir/tokens/${base_file//.$target/.tok.$target}"
    if [ ! -s "$tokens_file" ]; then
        echo "Encoding $file..."
        "$SUBTITLE_REPO/spm/spm_encode.py" \
        --model="$target_model_file" \
        --input="$file" \
        --output="$tokens_file" \
        --line-count="$line_count" \
            || exit 1
    fi
done

# Fairseq preprocessing
echo "Preprocessing..."
mkdir -p "$dir/preprocessed"
count=$(ls "$dir/preprocessed" | wc -l)
if [ "$count" -lt 2 ]; then
    fairseq-preprocess \
        --source-lang "$source" \
        --target-lang "$target" \
        --trainpref="$dir/tokens/train.tok" \
        --validpref="$dir/tokens/valid.tok" \
        --testpref="$dir/tokens/test.tok" \
        --destdir="$dir/preprocessed" \
        --optimizer="adam" \
            || exit 1
fi
echo "Done preprocessing. Ready for training."
