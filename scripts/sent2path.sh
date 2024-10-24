#!/usr/bin/env bash
# Given two .sent files (which has sentences on each line with no spaces), one for source and one for target
# this script will generate the .path file which is used to align the sentences (see path2align.py).
#
if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Usage: $0 [source] [target] [--skip-to-embed]"
    exit 1
fi

overlap_size=4

source="$1"
target="$2"

source_overlap="${source/.sent/.overlap}"
target_overlap="${target/.sent/.overlap}"

source_emb="${source/.sent/.emb}"
target_emb="${target/.sent/.emb}"

for arg in "$@"
do
    if [ "$arg" == "--skip-to-embed" ]; then
        skip_to_embed=1
    fi
done

if [ -z "$skip_to_embed" ]; then
    rm -f "$source_overlap" "$source_emb" "$target_overlap" "$target_emb" 2>/dev/null

    ./vecalign/overlap.py -n $overlap_size -i "$source" -o "$source_overlap"
    echo "Generated overlaps of $overlap_size to $source_overlap" 1>&2

    ./vecalign/overlap.py -n $overlap_size -i "$target" -o "$target_overlap"
    echo "Generated overlaps of $overlap_size to $target_overlap" 1>&2
else
    rm "$source_emb" "$target_emb" 2>/dev/null
fi

if [ -z "$LASER" ]; then
    echo "Please set LASER env var to LASER repository."
    exit 1
fi

$LASER/tasks/embed/embed.sh "$source_overlap" "$source_emb" #2>/dev/null
#echo "Generated embeddings to $source_emb" 2>/dev/null

$LASER/tasks/embed/embed.sh "$target_overlap" "$target_emb" #2>/dev/null
#echo "Generated embeddings to $target_emb"

alignment_max_size=$(cat "$SUBTITLE_REPO/src/config.py" | grep 'AlignmentMaxSize' | cut -d= -f2 | tr -d ' ')
./vecalign/vecalign.py --alignment_max_size $alignment_max_size \
    --src "$source" \
    --tgt "$target" \
    --src_embed "$source_overlap" "$source_emb" \
    --tgt_embed "$target_overlap" "$target_emb" #2>/dev/null
