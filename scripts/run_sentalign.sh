
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
    exit 1
fi

if [ -z "$1" ] || [ -z "$2" ] ; then
    echo "Usage: $0 [source file] [target file]"
    exit 1
fi

SOURCE="$1"
TARGET="$2"
BASE_DIR=$(dirname $(dirname $SOURCE))
SOURCE_LANG=$(dirname $SOURCE | awk -F/ '{print $NF}')
TARGET_LANG=$(dirname $TARGET | awk -F/ '{print $NF}')
TITLE_NAME=$(echo "$BASE_DIR" | awk -F/ '{print $NF}')
#echo "SOURCE: $SOURCE"
#echo "TARGET: $TARGET"
echo "Detecting $SOURCE_LANG --> $TARGET_LANG in Dir: $BASE_DIR"

SOURCE_SENT="${SOURCE/.srt/.sent}"
TARGET_SENT="${TARGET/.srt/.sent}"
PATH_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-sentalign.path"
ALIGNMENTS_FILE="$BASE_DIR/${SOURCE_LANG}-${TARGET_LANG}-sentalign.txt"

if [ -z "$PYTHONPATH" ]; then
    echo "Setting PYTHONPATH to this directory."
    export PYTHONPATH=$(pwd)
fi

echo "Extracting sentences..."
$SUBTITLE_REPO/scripts/srt2sent.py -f "$SOURCE" -i > "$SOURCE_SENT"
echo "$SOURCE_SENT"

$SUBTITLE_REPO/scripts/srt2sent.py -f "$TARGET" -i > "$TARGET_SENT"
echo "$TARGET_SENT"

if [ -z "$SENT_ALIGN_DIR" ]; then
    echo "Please set SENT_ALIGN_DIR environment variable to the root of that repository."
    exit 1
fi

# Copy files to dirs where sentalign wants them

SENTALIGN_SOURCE_DIR="$SENT_ALIGN_DIR/data/$SOURCE_LANG"
SENTALIGN_TARGET_DIR="$SENT_ALIGN_DIR/data/$TARGET_LANG"

cp "$SOURCE_SENT" "$SENTALIGN_SOURCE_DIR/$TITLE_NAME.txt"
cp "$TARGET_SENT" "$SENTALIGN_TARGET_DIR/$TITLE_NAME.txt"

# Run sentalign

python "$SENT_ALIGN_DIR/files2align.py" -dir "$SENT_ALIGN_DIR/data" --source-language "$SOURCE_LANG"
echo "USING mps proc-device. If not on mac, set this to cuda or cpu in file: $0."
python "$SENT_ALIGN_DIR/sentAlign.py" -dir "$SENT_ALIGN_DIR/data" -sl "$SOURCE_LANG" -tl "$TARGET_LANG" --proc-device mps

# Extract the alignments to where we want them
cut -f1,2 "$SENT_ALIGN_DIR/data/output/$TITLE_NAME.txt.aligned" | sed -e 's/$/\n/g' | tr '\t' '\n' > "$ALIGNMENTS_FILE"

echo "$PATH_FILE"
echo "$ALIGNMENTS_FILE"
