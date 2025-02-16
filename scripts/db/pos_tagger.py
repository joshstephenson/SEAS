#!/usr/bin/env python

import MySQLdb
import argparse
import spacy
import time

es_nlp = spacy.load('es_core_news_md')

db = MySQLdb.connect("localhost", "root", "", "alignments")
cursor = db.cursor()


def find_or_create_verb(verb, lang, is_aux=False) -> int:
    if verb is None:
        raise 'No verb passed'
    cursor.execute(f"SELECT id from verbs where verb = '{verb}';")
    if cursor.rowcount == 0:
        aux_bit = 1 if is_aux else 0
        cursor.execute(f"INSERT INTO verbs (verb, lang, is_aux) VALUES ('{verb.lower()}', '{lang}', '{aux_bit}');")
        cursor.execute(f"SELECT id from verbs where verb = '{verb}';")
    return cursor.fetchone()[0]


def join_verb_with_alignment(alignment_id, verb_id, token):
    cursor.execute("INSERT INTO alignment_verbs (alignment_id, verb_id, token) VALUES (%s, %s, %s)",
                   (alignment_id, verb_id, token.lower()))
    db.commit()


def batch(offset, batch_size):
    cursor.execute(f"SELECT * from alignments LIMIT {batch_size} OFFSET {offset};")
    results = cursor.fetchall()
    for result in results:
        spanish = es_nlp(result[2].strip())
        # print(result[2])
        extras = []
        for token in spanish:
            if token.pos_ == 'VERB':
                verb_id = find_or_create_verb(token.lemma_, 'spa')
                join_verb_with_alignment(result[0], verb_id, token.text)
                # extras.append(f'{token.text}[{token.lemma_.upper()}]')
            elif token.pos_ == 'AUX':
                verb_id = find_or_create_verb(token.lemma_, 'spa', True)
                join_verb_with_alignment(result[0], verb_id, token.text)
        db.commit()


def main():
    cursor.execute("select count(id) from alignments;")
    count = cursor.fetchone()[0]
    index = 0
    batch_size = 100
    while index < count:
        batch(index, batch_size)
        index += batch_size
        print(index)
    cursor.close()


if __name__ == '__main__':
    main()
