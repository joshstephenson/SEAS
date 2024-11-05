#!/usr/bin/env bash
# Takes a directory (year) which has subdirs of titles. Each title has subdirs of lang codes
# 2024/Scream/eng For example
# Will walk the directory looking for language support (currently hard-coded to eng and spa)
# And will run all possible alignments (each language dir likely has more than one subtitle file representing the same
# title).
# At the end it will find the longest alignment file and delete the rest leaving just eng-spa.txt
#
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 [directory] [source lang] [target lang]"
    exit 1
fi
if [ -z "$PYTHONPATH" ]; then
    echo "You must set the PYTHONPATH environment variable."
    exit 1
fi
if [ -z "$LASER" ]; then
    echo "Please set LASER env var to LASER repository."
    exit 1
fi

findpath="$1"
source_lang="$2"
target_lang="$3"
find_best="$4"

stderrfile=/tmp/corpus_generator.err
corpus_file="$findpath/all.txt"
if [ -s "$corpus_file" ]; then
    lines=$(wc -l < "$corpus_file")
    echo "Corpus file exists: $corpus_file"
    echo "Lines: $lines"
    sleep 1
fi

if [ ! -d "$findpath" ]; then
    echo "You must provide the path to the directory of one of the years of films."
    exit 1
fi

has_language_support() {
    dir="$1"; shift
    langs="$@"
    for lang in $langs; do
        if [ ! -d "$dir/$lang" ]; then
            echo "$(basename "$dir") doesn't have support for $lang" >&2
            return 1
        fi
    done
    return 0
}

first_srt_for() {
    dir="$1"
    lang="$2"
    find "$dir/$lang" -name "*.srt" -exec ls -lS {} + | head -n1 | awk -F' ' '{print $NF}'
}

all_srt_for() {
    dir="$1"
    lang="$2"
    echo $(find "$dir/$lang/" -iname "*.srt")
}

run_best_alignments() {
    dir="$1"
    source_lang="$2"
    target_lang="$3"
    longest=
    for source_file in $(all_srt_for "$dir" "$source_lang"); do
        for target_file in $(all_srt_for "$dir" "$target_lang"); do
            ./scripts/run_vecalign.sh "$source_file" "$target_file" 2> "$stderrfile" || continue
            out_file="$dir/$source_lang-$target_lang-vecalign.txt"
            # fix_offset also runs run_vecalign, so we should have the alignments file already
            if [ -s "$out_file" ]; then
                count=$(wc -l < "$out_file")
                if [ -z "$longest" ] || [ "$count" -gt "$longest" ]; then
                    echo "Longest alignments: $count" >&2
                    longest="$count"
                    keeper="${out_file//.txt/_keeper.txt}"
                    cp "$out_file" "$keeper"
                fi
            else
                # If alignment fails, remove the output file
                rm -f "$out_file"
                if grep 'No module named' "$stderrfile"; then
                    echo "You need to activate the python environment" >&2
                else
                    echo "Error occurred running vecalign" >&2
                    cat "$stderrfile"
                fi
                exit 1
            fi
        done
    done
    mv "$keeper" "$out_file"
    cat "$out_file" >> "$corpus_file"
}

run_simple_alignments() {
    dir="$1"
    source_lang="$2"
    target_lang="$3"
    title="$4"
    source_file=$(first_srt_for "$dir" "$source_lang")
    target_file=$(first_srt_for "$dir" "$target_lang")
#    echo "$source_file"
#    echo "$target_file"

    ./scripts/run_vecalign.sh "$source_file" "$target_file" 2> "$stderrfile" || return 1
    out_file="$dir/$source_lang-$target_lang-vecalign.txt"
    if [ -s "$out_file" ]; then
        cat "$out_file" >> "$corpus_file"
        count=$(echo "$(wc -l < "$out_file")" / 3 | bc )
        count2=$(echo "$(wc -l < "$corpus_file")" / 3 | bc )
        echo "Appending $count from $title. Total: $count2."
    else
        echo "Failed to generate alignments: $out_file"
    fi
}

find "$findpath" -d 1 -type d | sort | while read -r dir; do
    title=$(head -n1 "$dir/info.txt" | sed 's/^title: //')
    if has_language_support "$dir" "$source_lang" "$target_lang"; then
        if [ ! -s "$dir/$source_lang-$target_lang-vecalign.txt" ]; then
            if [ -n "$find_best" ]; then
                run_best_alignments "$dir" "$source_lang" "$target_lang"
            else
                run_simple_alignments "$dir" "$source_lang" "$target_lang" "$title"
            fi
        else
            echo "Skipping $dir. $source_lang-$target_lang-vecalign.txt exists."
        fi
    fi
done