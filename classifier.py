#!/usr/bin/env python

import openai
import sys
import time
import yaml
from openai import OpenAI
import argparse

with open('openai_creds.yaml', 'r') as f:
    creds = yaml.load(f, Loader=yaml.FullLoader)['openai']
client = OpenAI(
    organization=creds['organization'],
    api_key=creds['api_key'],
    project=creds['project']
)

def align_classifications(text, classifications):
    pairs = text.split("\n\n")
    pairs = [pair.split("\n") for pair in pairs]
    classifications = [c.strip() for c in classifications.split("\n")]

    pairs = [{'english': pair[0], 'spanish': pair[1], 'en': 0, 'es': 0} for pair in pairs]
    for i, (pair, c) in enumerate(zip(pairs, classifications)):
        assert len(c) == 2
        pairs[i]['en'], pairs[i]['es'] = c[0], c[1]

    return pairs


def classify_pairs(pairs, offset=0, length=-1):
    assert offset >= 0 and offset < len(pairs)
    last = len(pairs) if length == -1 else offset + length
    pairs = pairs[offset:last]
    text = "\n\n".join(pairs)
    count = len(pairs)
    content = f"I am including {count} sentence pairs below. "
    content += """Each is separated by an empty line.
For each pair, the first line is English and the second line is Spanish. 
I would like you to determine whether each line contains figurative use of language such as metaphors, idiomatic expressions, etc.
For each pair I would like you to respond with two bits and only two bits.
The first bit is for english and the second bit is for spanish.
00 would indicate neither sentence contains figurative language.
10 would indicate that only the english contains figurative language. 
01 would indicate only the spanish contains figurative language.
11 would indicate that both languages contain figurative language. 
Put each two bit series on its own line and please don't include anything else in your response. You must send back exactly """ + str(
        count) + """ lines of 2 bits
and they must correspond to the language pairs sent. Here are the pairs:

""" + text
    request = client.chat.completions.create(
        model="gpt-4o-mini",  # gpt-4o, gpt-4o-mini
        messages=[{"role": "user", "content": content}],
    )

    classifications = None
    for choice in request.choices:
        classifications = choice.message.content
    print(classifications)
    _length = len(classifications.split("\n"))
    if _length != length:
        print(f'count was: {_length} but should have been {length}')
        print(classifications)
        exit(0)
    bits = [c.strip() for c in classifications.split("\n")]
    return [(int(c[0]), int(c[1])) for c in bits]


def save_classifications(text, classifications, output_file):
    classifications = align_classifications(text, classifications)
    # Write to output file
    with open(output_file, 'w') as f:
        for c in classifications:
            line = "\t".join([c['english'], c['spanish'], c['en'], c['es']])
            f.write(line + "\n")
            print(line)


def load_text_from_file(filename: str):
    with open(filename, 'r') as f:
        lines = f.read()
    return lines


def get_output_filename(filename: str):
    base = ".".join(filename.split('.')[:-1])
    return f'{base}.tsv'


def test_consistency_chatgpt(opts, offset = 0, num_runs = 10, num_pairs = 10):
    runs: [[(int, int)]] = []
    changes = {i: set() for i in range(num_pairs)}

    # run classifications
    for i in range(num_runs):
        runs.append(classify_pairs(pairs, offset, num_pairs))
        print('.' * num_pairs + '|', end = "")
        time.sleep(3)

    # find the uniques
    for run in runs:
        for i, pair in enumerate(run):
            changes[i].add(run[i])
            # if run[i] not in changes[i]:
            #     changes[i].append(run[i])

    for i, options in changes.items():
        count = len(options)
        if count > 1:
            print(f'({i}): changed {count} times. [{options}]')
            for item in pairs[i].split("\n"):
                print(f'\t{item}')


def main(opts):
    print(opts)
    text = load_text_from_file(opts.file)
    pairs = text.split("\n\n")
    classifications = classify_pairs(pairs)
    print(classifications)
    save_classifications(text, classifications, get_output_filename(opts.file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', type=str, help='filename to process')
    args = parser.parse_args()
    main(args)
    # text = load_text_from_file(args.file)
    # pairs = text.split("\n\n")
    # count = len(pairs)
    # for i in range(int(count/10)):
    #     test_consistency_chatgpt(args, i * 10, 10, 10)
    #     time.sleep(10)
