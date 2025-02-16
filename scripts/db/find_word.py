#!/usr/bin/env python

import MySQLdb
import argparse
import spacy

es_nlp = spacy.load('es_core_news_md')

db = MySQLdb.connect("localhost", "root", "", "alignments")
cursor = db.cursor()

def word(word, length, limit):
    cursor.execute(
        f"SELECT source, target FROM alignments WHERE target LIKE '% {word} %' AND length < {length} LIMIT {limit};")
    results = cursor.fetchall()
    print(f'Found {len(results)} results.')
    for result in results:
        spanish = es_nlp(result[1].strip())
        print()
        extras = []
        for token in spanish:
            if token.pos_ in ['VERB', 'AUX']:
                extras.append(f'{token.text}[{token.lemma_.upper()}]')
        print(result[1], '\n ', result[0])
        print(" ", " ".join(extras))
    cursor.close()

def verb(verb):

def main(args):
    if args.word is not None:
        word(args.word, args.length, args.limit)
    else if args.verb is not None:
        verb(args.verb)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", '--word', dest='word')
    parser.add_argument("-v", '--verb', dest='verb')
    parser.add_argument('-l', '--length', dest='length', required=False, default=80)
    parser.add_argument('-L', '--limit', dest='limit', required=False, default=10)
    opts = parser.parse_args()
    if opts.word is None and opts.verb is None:
        parser.error('Either --word or --verb is required.')
    main(opts)