#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

venv/bin/mypy --ignore-missing-imports findpaths.py
venv/bin/mypy --ignore-missing-imports example_usage.py
venv/bin/mypy --ignore-missing-imports example_usage_batch.py
