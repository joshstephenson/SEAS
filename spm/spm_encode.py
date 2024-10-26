#!/usr/bin/env python
################################################################################
# This script is meant to replicate the funcitonality of spm_train
# spm_encode
#   --model=[model_path] < [input_file] > [output_file] --alpha --sample
# OR
# spm_encode
#   --model=[model_path] --input=[input_file] --output=[output_file] ...
################################################################################
import argparse
import sentencepiece as spm
import sys
from tqdm import tqdm

def load_spm(existing_model, random_seed=None):
    if random_seed is not None:
        spm.set_random_generator_seed(random_seed)
    return spm.SentencePieceProcessor(model_file=existing_model)

def read_file(path):
    with open(path, encoding='utf-8') as f:
        yield from f

def main(args):
    processor = load_spm(args.model, args.random_seed)
    input_file = read_file(args.input) if type(args.input) == str else args.input
    output_file = open(args.output, 'w', encoding='utf-8') if type(args.output) == str else args.output

    out_type = str if args.output_format == "piece" else int

    if args.line_count == 0:
        sys.stderr.write("Pass --line_count for progress bar." + "\n")
    for line in tqdm(input_file, total=args.line_count):
        fields = line.strip().split("\t")
        out_fields = []
        for field in fields:
            tokens = processor.encode(field, out_type=out_type, enable_sampling=args.enable_sampling, alpha=args.alpha)
            out_fields.append(" ".join([str(t) for t in tokens]))
        output_file.write("\t".join(out_fields) + "\n")
    if type(args.output) == str:
        output_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, type=str)
    parser.add_argument("--input", type=str, required=False, default=sys.stdin)
    parser.add_argument("--output", type=str, required=False, default=sys.stdout)
    parser.add_argument("--output-format", type=str, default="piece", choices=["id", "piece"])
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--enable-sampling", action="store_true")
    # line count is for tqdm
    parser.add_argument("--line-count", type=int, default=0)
    parser.add_argument("--random-seed", type=int, required=False)
    args = parser.parse_args()
    main(args)
