In addition to the packages in requirements.txt, these scripts need to have these other projects available in your environment:

- ./LASER -> https://github.com/facebookresearch/LASER
- ./vecalign -> https://github.com/thompsonb/vecalign
- ./data -> OpenSubtitles data that has been processed by `import_from_opensubtitles.sh` script.

In your environment set the following variables:
- PYTHONPATH -> Path to root of this repository
- LASER -> Path to LASER

## Which script should you use for a given task?
#### You have a dump of subtitles from OpenSubtitles and you need to organize them by year to later generate alignments
Use `import_from_opensubtitles.py`. This is most likely the first thing you will do.

#### To generate a corpus of alignments between source and target languages
Use `corpus_generator.py`. Will need to pass directory of year imported from `import_from_opensubtitles.py` as well as a source and target file.

#### You want to generate alignments for a single title using vector embeddings
This is a multi-step process that involves quite a few things but you can use this script to facilitate all of that: `run_vecalign.py`. That script will run:
- either `srt2overlap.py` if partitioning is enabled or `srt2sent.py` if not
- `sent2path.sh` which leverages vecalign
- `path2align.py` which takes the path output from vecalign and creates the alignments which will be placed into a file like `eng-ger-vecalign.txt` which for each alignment will place the english on one line, the german on the next and a subsequent empty line.

#### You want to generate alignments for a single title using timecodes
Use `run_chronos.py`.

#### You want to evaluate the alignments generated earlier against gold standard alignments
Use `evaluate_alignments.py`.

#### You want to annotate gold labels
Use `annotator.py`. This essentially runs vector embeddings as a best first guess on the alignments and then allows an annotator to walk through them one by one editing them to generate the gold labeled data. This is much faster than manually doing it but still has the same quality.

## Script Overview
| Script | Description |
|--------|-------------|
| **annotator.py** | File to leverage vector embeddings to annotate gold labels. Run this file with arguments: -s SOURCE -t TARGET where SOURCE is the path to the source language subtitle file and TARGET is the path to the target language subtitle file. Use -i to ignore empty alignments (when no alignment possibility can be found). |
| cleanup.py | Script used to cleanup files generated during the alignment process. This includes .emb, .path, .sent and .txt files within each title directory. |
| **corpus_generator.py** | This is the script you would want to use to generate a lot of alignments from subtitle files. |
| evaluate_alignments.py | Use -g GOLD_FILE, -a ALIGNMENTS_FILE where GOLD_FILE is the path to the gold labeled data (probably in `gold` directory) and ALIGNMENTS_FILE is the file output by `run_vecalign.py` |
| **evaluate_all.py** | Evaluates all titles in `gold` subdirectory, printing true positives, false negatives, false positives, recall, precision, and F1 scores when done. |
| filter_alignments_by_length.py | For any alignments generated it will filter out any longer than given length. |
| fix_offset.py | If timestamps between two files differ by more than provided number of seconds, it will fix the timestamps of one by applying an offset. Uses vecalign to make a best guess as to what the alignments should be. |
| **import_from_opensubtitles.py** | OpenSubtitles provided a sharded directory structure which is unreadable to the human eye. For clarity, this script will take any year and export all the appropriate subtitle files for that year in a directory structure of:
./data/<YEAR>/<TITLE> and within those directories will have the available languages in ISO 639-3 (three letter codes). If OpenSubtitles provided more than one subtitle file of each year+title+language combination, they will all be in those sub-directories. |
| language_verifier.py | Verifies the language of files in provided path are correct, using the ISO 639-3 code from the file path. If it's incorrect, the file will be deleted. |
| path2align.py | Takes a .path file and generates alignments from it. |
| results_analyzer.py | *I believe this is unused and should be deleted.* |
| run_and_eval.py | Allows running of alignments on a given title between two given language pairs using either `chronos` (timecode only alignment), `sentalign` or `vecalign`. |
| run_chronos.py | Runs alignments between source and target files using timecodes only. No vector embeddings. |
| run_sentalign.sh | Runs alignments between source and target files using Sentalign (if available). |
| **run_vecalign.py** | Runs alignments between source and target files using Vecalign. It uses whatever configuration variables are in `src/config.py` regarding sterilization (preprocessing), sentence boundary detection, partitioning, overlap size (for vecalign), gap threshold (for partitioning), alignment max size and merge ellipsized sentences. |
| sent2path.py | Runs vecalign to generate a hypothesize path (alignments) on two sentence files. |
| split_alignments.sh | Splits a file that has alignments between two languages in one file into two separate files with file extensions of the language ISO codes. |
| split_and_align.sh | Splits pairs of subtitle files based on gaps in the dialogue and then runs alignment. This should be called partitioning to disambiguate it from the above. |
| split_srt.py | Splits pairs of subtitle files based on gaps in the dialogue. |
| srt2overlap.py | If partitioning is enabled in `src/config.py`, this will partition, extract sentences, and then generate overlaps, ensuring not to generate overlaps across partitions. |
| srt2sent.py | If partitioning is not enabled in `src/config.py`, this will extract sentences from srt files, and then generate overlaps. |
| uber_script.py | *I believe this is unused and should be deleted.* |
| verify_alignments.py | *This script might also be unused.* |
