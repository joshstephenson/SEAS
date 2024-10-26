#!/usr/bin/env python
################################################################################
# This script is meant to replicate the funcitonality of spm_train
# spm_train
#   --input="${ALL_DETOK_PATH}"
#   --model_prefix="${VOCAB_DIR}/${VOCAB_PREFIX}"
#   --vocab_size="${VOCAB_SIZE}"
#   --character_coverage="${CHAR_COV}"
#   --model_type="${MODEL_TYPE}"
#   --shuffle_input_sentence=true
################################################################################

import argparse
import sentencepiece as spm
import sys


def data_iter(path):
    with open(path, "r", encoding='utf-8') as f:
        yield from f

def train_spm(model_prefix, train_iter, vocab_size, character_coverage, model_type, byte_fallback, random_seed=None, user_defined_symbols=""):
    if random_seed is not None:
        spm.set_random_generator_seed(random_seed)
    spm.SentencePieceTrainer.train(
        sentence_iterator=train_iter,
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        character_coverage=character_coverage,
        model_type=model_type,
        byte_fallback=byte_fallback,
        shuffle_input_sentence=True,
        user_defined_symbols=user_defined_symbols
    )
    return spm.SentencePieceProcessor(model_file=model_prefix + ".model")

def main(args):
    sentences = data_iter(args.input)
    processor = train_spm(
        args.model_prefix,
        sentences,
        args.vocab_size,
        args.character_coverage,
        model_type=args.model_type,
        byte_fallback=args.byte_fallback,
        random_seed=args.random_seed,
        user_defined_symbols=args.user_defined_symbols
    )
    sys.stderr.write(f'Vocab model written to: {args.model_prefix}.model')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=str)
    parser.add_argument("--model-prefix", required=True)
    parser.add_argument("--vocab-size", type=int, default=8000)
    parser.add_argument("--character-coverage", type=float, default=0.9995)
    parser.add_argument("--model-type", type=str, default="unigram")
    parser.add_argument("--byte-fallback", action="store_true", default=False)
    parser.add_argument("--random-seed", type=int, required=False)
    parser.add_argument("--user-defined-symbols", type=str, default="")
    args = parser.parse_args()
    main(args)
