# Setup
In addition to the packages in requirements.txt, these scripts need to have these other projects available in your environment:

- `./LASER` → [facebookresearch/LASER](https://github.com/facebookresearch/LASER)  
- `./vecalign` → [thompsonb/vecalign](https://github.com/thompsonb/vecalign)  
- `./data` → OpenSubtitles data processed by `import_from_opensubtitles.sh`

## Environment Variables

Set the following in your environment:

- **PYTHONPATH** → Path to the root of this repository  
- **LASER** → Path to LASER

---

# Which Script Should You Use?

### Organize OpenSubtitles dump by year
**Script:** `import_from_opensubtitles.py`  
**When:** First step when working with OpenSubtitles data.

### Generate a corpus of alignments between two languages
**Script:** `corpus_generator.py`  
**Usage:**  
```bash
corpus_generator.py data/2024 eng ger
```

- data/2024 comes from import_from_opensubtitles.py
- Output: data/2024/all.eng and data/2024/all.ger
- Lines correspond across files (line n in .eng aligns with line n in .ger).


### Generate alignments for a single title using vector embeddings
**Script:** `run_vecalign.py`  
This script automates:  
1. `srt2overlap.py` (if partitioning is enabled) **or** `srt2sent.py` (if not)  
2. `sent2path.sh` (uses vecalign)  
3. `path2align.py` (produces `eng-ger-vecalign.txt` with: English line → German line → blank line)

---

### Generate alignments for a single title using timecodes only
**Script:** `run_chronos.py`

---

### Evaluate generated alignments against gold standard
**Script:** `evaluate_alignments.py`

---

### Annotate gold labels
**Script:** `annotator.py`  
Uses vector embeddings for an initial guess, then lets an annotator step through and edit alignments. Faster than manual creation while preserving quality.

---

# Script Overview

| Script | Description |
|--------|-------------|
| **annotator.py** | Leverages vector embeddings to annotate gold labels. Args: `-s SOURCE` and `-t TARGET` for paths to subtitle files. Use `-i` to ignore empty alignments. |
| cleanup.py | Cleans `.emb`, `.path`, `.sent`, and `.txt` files from title directories. |
| **corpus_generator.py** | Generates bulk alignments from subtitle files. |
| evaluate_alignments.py | Compare generated alignments to gold. Args: `-g GOLD_FILE` and `-a ALIGNMENTS_FILE`. |
| **evaluate_all.py** | Evaluates all titles in `gold/`, printing TP, FN, FP, recall, precision, and F1. |
| filter_alignments_by_length.py | Removes alignments longer than a given length. |
| fix_offset.py | Adjusts subtitle timestamps if they differ by more than a given number of seconds, using vecalign to guide the fix. |
| **import_from_opensubtitles.py** | Converts OpenSubtitles’ sharded directory structure into `./data/<YEAR>/<TITLE>` with ISO 639-3 language files. Multiple files for the same (year, title, language) are kept together. |
| language_verifier.py | Checks file language matches ISO 639-3 code in its path. Deletes incorrect files. |
| path2align.py | Converts `.path` files into alignments. |
| results_analyzer.py | *(Likely unused — consider deletion)* |
| run_and_eval.py | Runs alignments for a given title/language pair using `chronos`, `sentalign`, or `vecalign`. |
| run_chronos.py | Timecode-only alignments (no embeddings). |
| run_sentalign.sh | Alignments using Sentalign (if installed). |
| **run_vecalign.py** | Vecalign-based alignments using config in `src/config.py` (preprocessing, sentence splitting, partitioning, overlaps, thresholds, etc.). |
| sent2path.py | Runs vecalign to produce a `.path` alignment file. |
| split_alignments.sh | Splits a bilingual alignment file into two files with language-specific extensions. |
| split_and_align.sh | Splits subtitle pairs by dialogue gaps, then runs alignment (partitioning). |
| split_srt.py | Splits subtitle pairs by dialogue gaps. |
| srt2overlap.py | Partitions (if enabled), extracts sentences, and generates overlaps — avoiding overlaps across partitions. |
| srt2sent.py | Extracts sentences and generates overlaps when partitioning is disabled. |
| uber_script.py | *(Likely unused — consider deletion)* |
| verify_alignments.py | *(Possibly unused)* |
