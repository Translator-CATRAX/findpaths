#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

rm -r -f venv
python3.10 -m venv venv
venv/bin/pip3 install -r requirements.txt

venv/bin/mypy --ignore-missing-imports findpaths.py

curl -O -s https://kg2webhost.rtx.ai/kg2c-2.8.4-edges-lite.jsonl.gz
mv kg2c-2.8.4-edges-lite.jsonl.gz kg2c-2.8.4-edges.jsonl.gz
curl -O -s https://kg2webhost.rtx.ai/kg2c-2.8.4-nodes-lite.jsonl.gz
mv kg2c-2.8.4-nodes-lite.jsonl.gz kg2c-2.8.4-nodes.jsonl.gz

venv/bin/python findpaths.py --writePickle kg2c-2.8.4
