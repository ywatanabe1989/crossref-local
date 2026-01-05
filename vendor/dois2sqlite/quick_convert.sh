#!/bin/env bash


# define verbosity
verbosity="--verbose"

# Define file paths
# tar_file="testdata/250k.json.tar"
# sqlite3_file="testdata/250k.sqlite3"
#tar_file="/mnt/4tb/some.json.tar"
# sqlite3_file="/mnt/4tb/some.sqlite3"
tar_file="/mnt/4tb/all.json.tar"
sqlite3_file="/mnt/4tb/all.sqlite3"


function run_cr2sqlite3_ng() {
    time python dois2sqlite/cli.py "$@"
}

rm "$sqlite3_file"
run_cr2sqlite3_ng create "$sqlite3_file" "$verbosity"
run_cr2sqlite3_ng load "$tar_file" "$sqlite3_file" --n-jobs 32 --convert-to-commonmeta "$verbosity"
run_cr2sqlite3_ng index "$sqlite3_file" "$verbosity"
