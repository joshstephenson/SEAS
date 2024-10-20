#!/usr/bin/env bash
# Generate the alignments for a given language pair using vecalign scripts
# Compare against gold standard if available

find_largest_srt() {
    local directory=$1
    find "$directory" -name "*.srt" -exec ls -lS {} + | head -n1 | awk -F' ' '{print $NF}'
}

run_method() {
    if [ "$1" == "chronos" ]; then
        ./scripts/run_chronos.py -s "$2" -t "$3" > "$4"
    elif [ "$1" == "sentalign" ]; then
        ./scripts/run_sentalign.sh "$2" "$3"
    elif [ "$1" == "vecalign" ]; then
        ./scripts/run_vecalign.sh "$2" "$3"
    fi
}

evaluate() {
    ./scripts/evaluate_alignments.py -g "$1" -a "$2" # -fp -fn -tp
}

# Main function to process languages and directories
main() {
    method="$1"
    virtual_dir=~/.virtual/$method
    if [ -d $virtual_dir ] || [ -L $virtual_dir ]; then
        echo "Activating $method Environment"
        source "$virtual_dir/bin/activate"
    else
        echo "Please create a virtual environment to be used at '~/.virtual/$method'"
        exit 1
    fi

    if [ -z "$PYTHONPATH" ]; then
        echo "Setting PYTHONPATH to this directory."
        export PYTHONPATH=$(pwd)
    fi
    directory=$2
    source_lang=$3
    target_lang=$4
    gold_file="$directory/$source_lang-$target_lang-gold.txt"
    output_file="$directory/$source_lang-$target_lang-$method.txt"
    results_file="$directory/$source_lang-$target_lang-$method.results"

    source_dir="${directory}/${source_lang}"
    target_dir="${directory}/${target_lang}"
    source_file=$(find_largest_srt "$source_dir")
    target_file=$(find_largest_srt "$target_dir")

    if [ ! -f "$gold_file" ]; then
        echo "No gold file found at $gold_file"
        exit 1
    fi
    if run_method "$method" "$source_file" "$target_file" "$output_file"; then
        if evaluate "$gold_file" "$output_file" > "$results_file" ; then
            echo "Results written to: $results_file"
            cat "$results_file"
        else
            echo "Error with evaluation."
        fi
    fi
}

usage() {
    echo "Usage: $0 [chronos|sentalign|vecalign] [directory] [source lang code] [target lang code]"
    exit 1
}

# Ensure two languages were provided
if [ "$#" -ne 4 ]; then
    usage
fi
if [ "$1" != "chronos" ] && [ "$1" != "vecalign" ] && [ "$1" != "sentalign" ]; then
    usage
fi

main "$1" "$2" "$3" "$4"