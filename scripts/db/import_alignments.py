#!/usr/bin/env python

import MySQLdb
import argparse
import spacy

es_nlp = spacy.load('es_core_news_md')

db = MySQLdb.connect("localhost", "root", "", "alignments")
cursor = db.cursor()

def main(args):
    with open(args.source, "r") as f:
        source_lines = f.readlines()
    with open(args.target, "r") as f:
        target_lines = f.readlines()

    if len(source_lines) != len(target_lines):
        raise(f"Source and target files must have same number of lines. Source: {len(source_lines)}, target: {len(target_lines)}")
    #
    # for sl, tl in zip(source_lines[:10], target_lines[:10]):
    #     spanish = es_nlp(tl.strip())
    #     print()
    #     extras = []
    #     for token in spanish:
    #         if token.pos_ in ['VERB', 'AUX']:
    #             extras.append(f'{token.text}[{token.lemma_.upper()}]')
    #
    #     print(sl, tl, " ".join(extras))

    for source_line, target_line in zip(source_lines, target_lines):
        longest = max(len(source_line), len(target_line))

        cursor.execute(f"INSERT INTO alignments (source, target, length, source_lang, target_lang) VALUES (%s, %s, %s, 'eng', 'spa');",
                       (source_line.strip(), target_line.strip(), longest)
                       )
    db.commit()
    cursor.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="Source file with alignments", required=True)
    parser.add_argument("-t", "--target", help="Target file with alignments", required=True)
    
    opts = parser.parse_args()
    main(opts)