#!/usr/bin/env bash

if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Usage: $0 [source] [target]"
    exit 1
fi

OVERLAP_SIZE=4

SOURCE="$1"
TARGET="$2"

SOURCE_OVERLAP="${SOURCE/.sent/.overlap}"
TARGET_OVERLAP="${TARGET/.sent/.overlap}"

SOURCE_EMB="${SOURCE/.sent/.emb}"
TARGET_EMB="${TARGET/.sent/.emb}"

rm -f "$SOURCE_OVERLAP" "$SOURCE_EMB" "$TARGET_OVERLAP" "$TARGET_EMB"

./vecalign/overlap.py -n $OVERLAP_SIZE -i "$SOURCE" -o "$SOURCE_OVERLAP"
echo "Generated overlaps of $OVERLAP_SIZE to $SOURCE_OVERLAP" 1>&2

./vecalign/overlap.py -n $OVERLAP_SIZE -i "$TARGET" -o "$TARGET_OVERLAP"
echo "Generated overlaps of $OVERLAP_SIZE to $TARGET_OVERLAP" 1>&2

./LASER/tasks/embed/embed.sh "$SOURCE_OVERLAP" "$SOURCE_EMB" 2>/dev/null
#echo "Generated embeddings to $SOURCE_EMB" 2>/dev/null

./LASER/tasks/embed/embed.sh "$TARGET_OVERLAP" "$TARGET_EMB" 2>/dev/null
#echo "Generated embeddings to $TARGET_EMB"

./vecalign/vecalign.py --alignment_max_size 8 \
    --src "$SOURCE" \
    --tgt "$TARGET" \
    --src_embed "$SOURCE_OVERLAP" "$SOURCE_EMB" \
    --tgt_embed "$TARGET_OVERLAP" "$TARGET_EMB" 2>/dev/null
