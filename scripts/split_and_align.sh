#!/usr/bin/env bash
#
# First splits SRT files into groups based on significant gaps in the timecodes
# Based on those gaps in the source file, it finds corresponding groups in target SRT file
# Files are saved with original file names with an infix '-NUM' where NUM is a 3 digit number
#
# After that, this file runs both timecode basad alignments and vector embedding alignments and then uses
# results_analyzer.sh to find overlap.
#
if [ -z "$SUBTITLE_REPO" ]; then
    echo "Please set SUBTITLE_REPO environment variable to the root of this repository."
fi
if [ "$#" -ne 4 ] ; then
    echo "Usage: $0 [title dir] [source lang code] [target lang code] [split gap length]"
    exit 0
fi

base_dir="$1"
source_lang="$2"
target_lang="$3"
split_gap_length="$4"

# Find subtitle files
# Subtile files are 8 or more digits with an .srt extension
source=$(find -E "$base_dir/$source_lang" -iregex ".+[0-9]{8,}.srt" -exec ls -S {} \; | tail -n 1)
target=$(find -E "$base_dir/$target_lang" -iregex ".+[0-9]{8,}.srt" -exec ls -S {} \; | tail -n 1)
echo "source: $source"
echo "target: $target"

# Remove old splits
$SUBTITLE_REPO/scripts/cleanup.sh "$base_dir"

# Now split them
$SUBTITLE_REPO/scripts/split_srt.py -s "$source" -t "$target" -g "$split_gap_length"

#source_files=$(find -E "$base_dir/$source_lang" -iregex '.+-[0-9]{3}.srt' | sort)
mapfile -t source_files < <(find -E "$base_dir/$source_lang" -iregex '.+-[0-9]{3}.srt' | sort)
echo "Generated ${#source_files[@]} splits"

# First do the align script for timecode-based alignments
# We don't split the files for this
time_file="$base_dir/${source_lang}-${target_lang}-chronos.txt"
$SUBTITLE_REPO/scripts/run_chronos.py -s "$source" -t "$target" > "$time_file"

for source in "${source_files[@]}"; do
    infix=$(echo $source | cut -d- -f2 | cut -d. -f1)
    target="$(find -E "$base_dir/$target_lang" -iregex ".+[0-9]{8,}-$infix.srt" -exec ls -S {} \; | tail -n 1)"
    source_sent="${source/.srt/.sent}"
    target_sent="${target/.srt/.sent}"
    path_file="$base_dir/${source_lang}-${target_lang}-vecalign-${infix}.path"
    alignments_file="$base_dir/${source_lang}-${target_lang}-vecalign-${infix}.txt"
#    echo "$source"
#    echo "$target"
#    echo "$source_sent"
#    echo "$target_sent"
#    echo "$time_file"
#    echo "$path_file"
#    echo "$alignments_file"

    # Skip this Split because it doesn't have any subtitles to align
    if [ ! -s "$source" ] || [ ! -s "$target" ]; then
        echo "SKIPPING ${infix}" >&2
        continue
    else
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$source" -l "$source_lang" > "$source_sent"
        "$SUBTITLE_REPO/scripts/srt2sent.py" -f "$target" -l "$target_lang" > "$target_sent"
        # Even though the subtitle file wasn't empty, the sent file still can be if everything was scrubbed in preprocessing
        if [ ! -s "$source_sent" ] || [ ! -s "$target_sent" ]; then
            echo "SKIPPING ${infix} after sentence generation." >&2
            continue
        fi
    fi
    echo "SPLIT: $infix"

    echo "$target_sent"
    if [ ! -s "$path_file" ]; then
        if ! "$SUBTITLE_REPO/scripts/sent2path.sh" "$source_sent" "$target_sent" | grep -v "| INFO |" > "$path_file"; then
            echo "Failed to generated path file."
            exit 1
        fi
    fi
    echo "$path_file"
    if [ ! -s "$alignments_file" ]; then
        if ! "$SUBTITLE_REPO/scripts/path2align.py" -s "$source_sent" -t "$target_sent" -p "$path_file" > "$alignments_file"; then
            echo "Failed to generate alignments f ile."
            exit 1
        fi
    fi
done
alignments_file="$base_dir/$source_lang-$target_lang-vecalign.txt"
gold_file="$base_dir/$source_lang-$target_lang-gold.txt"

# Combine the vector alignments
cat "$base_dir/$source_lang-$target_lang"-vecalign-*.txt > "$alignments_file"

#"$SUBTITLE_REPO/scripts/results_analyzer.py" -f "$time_file" "$alignments_file" -o "$gold_file" -a


