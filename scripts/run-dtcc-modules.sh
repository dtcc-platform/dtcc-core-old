#!/bin/bash


run_function() {
    echo "Running $1"
    if $1; then
        echo "Successfully excecuted! $1"
    else
        echo "Failed to excecuting!! $1"
    fi
}


files=(/wrappers/*.py)
for file in "${files[@]::${#files[@]}-1}" ; do
    # Non-blocking background processes
    echo "Starting $file" 
    python3 $file &
done
# blocking background process
run_function "python3 ${files[@]: -1:1}"