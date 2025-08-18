# Subtitle Alignment
 
## About
Applying state-of-the-art sentence alignment tools to subtitle extraction and alignment, achieving a substantial improvement in subtitle alignment quality. Leveraging sentence embeddings, dynamic programming, cosine similarity, and partitioning we attained F1 scores exceeding 93\% and estimate an overall improvement of 31\% based on other subtitle alignment techniques.

## Scripts for preprocessing and aligning subtitles
The directory `scripts` has all the necessary tools to import subtitles from a directory structure provided by OpenSubtitles, align sentences, run evaluation against gold-labeled alignments, etc. See README in `scripts` directory for usage.

## Gold Standard Subtitle Alignments
There are gold alignments for 5 titles in the `gold` directory. The alignments can be found within each subdirectory with names like `eng-spa-gold.txt` and `eng-ger-gold.txt`. The subtitles themselves are in the sub directories `eng`, `spa`, `ger`, etc.

## SubAlign Annotation tool
There is a curses and python implementation of an annotation tool. You must first run the script (`scripts/run_vecalign.py`) on the title you want to annotate in order to generate the hypothesis alignments. Then the annotation tool (`scripts/annotator.py`) will load those alignments into a vim-like editor where you can approve, edit or delete them. This tool supports the following operations:

| Key | Action|
|--------|-----|
|d| **D**elete current alignment.|
|e| **E**dit current alignment. Will open the current alignment in Vim.|
|u| **Union** (merge) current subtitle with the following subtitle|
|s| **Split** alignment into two. This will actually duplicate the current alignment allowing you to edit it and the subsequent (duplicate). Ideal for splitting alignments when multiple sentencese have been merged together.|
|w| **Write** (save) all alignments including those that have not yet been reviewed.|
|n| Move to **N**ext alignment.|
|p| Move to **P**revious alignment.|

<img width="1286" alt="Captura de pantalla 2024-11-10 a la(s) 11 34 29" src="https://github.com/user-attachments/assets/07404f61-ebf1-4003-abfa-0b28455bc102">

## What alignments look like
Once alignments are generated they will look like the following (2 separate files where the line numbers correspond):
<img width="1418" height="982" alt="Captura de pantalla 2025-08-18 a la(s) 09 41 20" src="https://github.com/user-attachments/assets/f4889691-3b20-48ec-b9b1-69c584f03aba" />
