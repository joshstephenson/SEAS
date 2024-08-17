# LanguageFlashCardsFromSubtitles
 
## About
The purpose of this project is to create pairs of utterances in two languages using SRT subtitle files.


## Usage
```
./cards_from_subs.py 
    --source data/TheShawshankRedemption_en.srt 
    --target data/TheShawshankRedemption_es.srt 
    --sterilize
```

Sample output:
```
- Not a word.
- Ni una palabra.

- Lord, it's a miracle!
- ¡Dios! ¡Es un milagro!

- A man up and vanished like a fart in the wind.
- ¡El hombre se desvaneció como un pedo en el viento!

- Nothing left but...
- Nada quedó excepto...

- some damn rocks on a windowsill.
- ...unas malditas rocas en la ventana.

- And that cupcake on the wall. Let's ask her.
- Y esa nalguita en la pared. Preguntémosle a ella.

- Maybe she knows. What say there, Fuzzy Britches? Feel like talking?
- Quizás ella lo sabe. Qué dices, a ver chulita ¿Quieres hablar? Ah...
```

#### Arguments
- --sterilize removes all content in between parethensis, curly brackets and HTML tags. It also strips leading hypens.
- --offset allows for providing an offset between source and target subtitles. Sometimes one file has more quite space at the beginning or they timecodes don't quite match for whatever reason. Use the SRT timecode format of `00:00:00,000` to specify the offset. A positive value means the target subtitles are behind (timecodes are larger) than the source.
- --offset-is-negative indicates that the source subtitles are behind the target subtitles.

## Considerations
Associating subtitles requires multiple considerations:
1. The subtitles for each language need to be loaded into memory, skipping any empty subtitles. If the sterilize argument is provided (recommended), the subtitle text is sterilized (see above argument) before checking content lentgth.
2. The timecodes need to be parsed and turned into a number of milliseconds since the beginning of the video. These are used to align subtitles.
3. Merging of subtitles. Often individual utterances (sentences) are spread across numerous subtitles. For usage in a language corpus it is useful to merge these into individual sentences.
3. Target language subtitles are associated with source language. For each subtitle in the source language a subtitle pair in the target language is found using the timecodes. This gets tricky when what is said in one sentences in one language requires multiple sentences in another. In this instance, more heuristics are required to merge them appropriately.
