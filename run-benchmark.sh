#!/usr/bin/env bash

# to pass multiple cutoffs, you would do this:  --cutoff 3 4
# (i.e., add a space between each integer cutoff value).
#
# Default language is python. To change language to c++, just
# pass "cxx" as the first argument to this bash script, like this:
#     ./run-benchmark.h cxx

venv/bin/python3 findpaths.py kg2c-2.8.4 \
                 --readPickle \
                 --multiNodeFileName test-data-file.txt \
                 --lang ${1:-python}






