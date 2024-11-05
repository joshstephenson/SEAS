#!/usr/bin/env bash
source "$(dirname $0)/base.sh"

usage() {
    echo "Usage: $0 [alignments filename]"
    exit 1
}

if [ "$#" -lt 1 ] || [ ! -f "$1" ]; then
    usage
fi
filename="$1"

source_file="$IN_DIR/all.$SOURCE"
target_file="$IN_DIR/all.$TARGET"
echo "$source_file"
if [ ! -s "$source_file" ]; then
    count=1
    echo "Extracting alignments..."
    # Alignments are in a single file in lines of 3. The first line is the SOURCE file
    # The second line is the TARGET and the third is an empty line for separation.
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
if [ ! -s "$IN_DIR/train.$SOURCE" ]; then
    # Get the total number of lines
    total_lines=$(wc -l < "$source_file")

    # Calculate line counts for each split
    train_lines=$((total_lines * 80 / 100))
    val_lines=$((total_lines * 10 / 100))
    test_lines=$((total_lines - train_lines - val_lines))

    # Split the file
    head -n "$train_lines" "$source_file" > "$IN_DIR/train.$SOURCE"
    head -n "$train_lines" "$target_file" > "$IN_DIR/train.$TARGET"

    tail -n +"$((train_lines + 1))" "$source_file" | head -n "$val_lines" > "$IN_DIR/valid.$SOURCE"
    tail -n +"$((train_lines + 1))" "$target_file" | head -n "$val_lines" > "$IN_DIR/valid.$TARGET"

    tail -n "$test_lines" "$source_file" > "$IN_DIR/test.$SOURCE"
    tail -n "$test_lines" "$target_file" > "$IN_DIR/test.$TARGET"
fi

# Now we can tokenize them
source_model_file="$DIR/$SOURCE.model"
target_model_file="$DIR/$TARGET.model"
source_vocab_file="$DIR/$SOURCE.vocab"
target_vocab_file="$DIR/$TARGET.vocab"
if [ ! -s "$source_model_file" ] || [ ! -s "$target_model_file" ]; then
    for set in $SOURCE $TARGET; do
        echo "Training $set tokenizer..."
        "$SUBTITLE_REPO/spm/spm_train.py" \
            --input="$IN_DIR/all.$set" \
            --model-prefix="$DIR/$set" \
            --vocab-size="$VOCAB_SIZE" \
            --model-type='bpe' \
            || exit 1
        # Omitting special tokens <unk>, <s>, </s> replace all numbers in 2nd column with 100
        tail -n +4 "$DIR/${set}.vocab" | cut -f 1 | sed "s/$/ 100/g" > "$DIR/${set}.vocab.tmp"
        mv -f "$DIR/${set}.vocab.tmp" "$DIR/${set}.vocab"
    done
fi
echo -e "\nFinished training tokenizers: $SOURCE $TARGET"

# Now tokenize the files with the tokenizer
for set in $SOURCE $TARGET; do
    find "$DIR" | grep -E ".+\.$set" | grep -v '.tok.' | grep -v 'all' | while read -r file; do
        line_count=$(wc -l < "$file" | tr -d ' ')
        base_file=$(basename "$file")
        tokens_file="$TOKENS_DIR/${base_file//.$set/.tok.$set}"
        if [ ! -s "$tokens_file" ]; then
            echo "Encoding $file..."
            "$SUBTITLE_REPO/spm/spm_encode.py" \
            --model="$DIR/${set}.model" \
            --input="$file" \
            --output="$tokens_file" \
            --line-count="$line_count" \
                || exit 1
        fi
    done
done

# Fairseq preprocessing
echo "Preprocessing..."
mkdir -p "$PREPROCESSED_DIR"
count=$(ls "$PREPROCESSED_DIR" | wc -l)
if [ "$count" -lt 2 ]; then
    fairseq-preprocess \
        --source-lang "$SOURCE" \
        --target-lang "$TARGET" \
        --srcdict="$source_vocab_file" \
        --tgtdict="$target_vocab_file" \
        --seed "$SEED" \
        --thresholdsrc=1 \
        --thresholdtgt=1 \
        --trainpref="$TOKENS_DIR/train.tok" \
        --validpref="$TOKENS_DIR/valid.tok" \
        --testpref="$TOKENS_DIR/test.tok" \
        --destdir="$PREPROCESSED_DIR" \
            || exit 1
fi
echo "Done preprocessing. Ready for training."
