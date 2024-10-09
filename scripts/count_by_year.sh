#!/usr/bin/env bash
# Assumes there's a sqlite database called subtitles.db
YEAR=2000
echo "YEAR, FILES, TITLES"
while [[ $YEAR -lt 2025 ]];do
    COUNT=$(sqlite3 "$SUBTITLE_DATA/subtitles.db" "select count(*) from subtitles where year='$YEAR';")
    UNIQ=$(sqlite3 "$SUBTITLE_DATA/subtitles.db" "select count(*) as combo from (select distinct title from subtitles where year='$YEAR');")
    echo "$YEAR, $COUNT, $UNIQ"
    YEAR=$(($YEAR+1))
done
