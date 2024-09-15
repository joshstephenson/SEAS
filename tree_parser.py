#!/usr/bin/env python

import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')

from nltk import pos_tag, word_tokenize, RegexpParser

en_text = "We see by your file you've served 20 years of a life sentence."
es_text = "Vemos en su archivo que ha cumplido 20 años de cadena perpetua."

en_tagged = pos_tag(word_tokenize(en_text))
es_tagged = pos_tag(word_tokenize(es_text))

chunker = RegexpParser("""
                       NP: {<DT>?<JJ>*<NN>}    #To extract Noun Phrases
                       P: {<IN>}               #To extract Prepositions
                       V: {<V.*>}              #To extract Verbs
                       PP: {<p> <NP>}          #To extract Prepositional Phrases
                       VP: {<V> <NP|PP>*}      #To extract Verb Phrases
                       """)

en_output = chunker.parse(en_tagged)
es_output = chunker.parse(es_tagged)
# en_output.draw()
es_output.draw()

output = chunker.parse()
