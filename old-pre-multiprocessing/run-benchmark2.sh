#!/usr/bin/env bash

# Default language is python. To change language to c++, just
# pass "cxx" as the first argument to this bash script, like this:
#     ./run-benchmark2.h cxx

# 96 GiB of system memory needed to run this script

venv/bin/python3 findpaths.py kg2c-2.8.4 \
                 --readPickle \
                 --startnode NCBIGene:9927 \
                 --endnode HP:0003474 \
                 --cutoff 4 \
                 --mult 12 \
                 --lang ${1:-python}
