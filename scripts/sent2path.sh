#!/usr/bin/env bash
# Given two .sent files (which has sentences on each line with no spaces), one for source and one for target
# this script will generate the .path file which is used to align the sentences (see path2align.py).
#
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi
if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Usage: $0 [source sentence file] [target sentence file] [--skip-to-embed]"
    exit 1
fi

overlap_size=4

source="$1"
target="$2"

if [[ ! "$source" =~ \.sent$ ]] || [[ ! "$target" =~ \.sent$ ]]; then
    echo "Source or target file do not have .sent extension. Appear not to be sentence files."
    exit 1
fi

source_overlap="${source/.sent/.overlap}"
target_overlap="${target/.sent/.overlap}"
rm -f "$source_overlap" "$target_overlap" 2>/dev/null

source_emb="${source/.sent/.emb}"
target_emb="${target/.sent/.emb}"
rm -f "$source_emb" "$target_emb" 2>/dev/null

for arg in "$@"
do
    if [ "$arg" == "--skip-to-embed" ]; then
        skip_to_embed=1
    fi
done

if [ -z "$skip_to_embed" ]; then
    "$SUBTITLE_REPO/vecalign/overlap.py" -n $overlap_size -i "$source" -o "$source_overlap" #2>/dev/null
    "$SUBTITLE_REPO/vecalign/overlap.py" -n $overlap_size -i "$target" -o "$target_overlap" #2>/dev/null
fi

if [ -z "$LASER" ]; then
    echo "Please set LASER env var to LASER repository."
    exit 1
fi

"$LASER/tasks/embed/embed.sh" "$source_overlap" "$source_emb" #2>/dev/null
if [ ! -s "$source_emb" ]; then
    echo "Failed to generate embeddings for source: $source_emb" >&2
    exit 1
fi

"$LASER/tasks/embed/embed.sh" "$target_overlap" "$target_emb" #2>/dev/null
if [ ! -s "$target_emb" ]; then
    echo "Failed to generate embeddings for target: $target_emb" >&2
    exit 1
fi
alignment_max_size=$(cat "$SUBTITLE_REPO/src/config.py" | grep 'AlignmentMaxSize' | cut -d= -f2 | tr -d ' ')
"$SUBTITLE_REPO/vecalign/vecalign.py" --alignment_max_size "$alignment_max_size" \
    --src "$source" \
    --tgt "$target" \
    --src_embed "$source_overlap" "$source_emb" \
    --tgt_embed "$target_overlap" "$target_emb" #2>/dev/null
