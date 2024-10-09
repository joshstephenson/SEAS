#!/usr/bin/env bash
# Finds pairs, triplets and quads of languages for unique titles

rm -f lang_support.txt
LANGS=(eng spa fre dut ita ger swe kor chi jpn)
for LG in ${LANGS[@]}; do
    echo -n "$LG: " >> lang_support.txt
    sqlite3 "$SUBTITLE_DATA/subtitles.db" "select count(*) as combo from (select distinct title from subtitles where lang in ('$LG'));" >> lang_support.txt
done

LANGS=(fre dut ita ger swe kor chi jpn)
for LG in ${LANGS[@]}; do
    echo -n "eng, spa, $LG: " >> lang_support.txt
    sqlite3 "$SUBTITLE_DATA/subtitles.db" "select count(*) as combo from (select title from subtitles where lang in ('eng', 'spa', '$LG') group by title having count(distinct lang) = 3);" >> lang_support.txt
done

LANGS=(dut ita ger swe kor chi jpn)
for LG in ${LANGS[@]}; do
    echo -n "eng, spa, fre, $LG: " >> lang_support.txt
    sqlite3 "$SUBTITLE_DATA/subtitles.db" "select count(*) as combo from (select title from subtitles where lang in ('eng', 'spa', 'fre', '$LG') group by title having count(distinct lang) = 4);" >> lang_support.txt
done
