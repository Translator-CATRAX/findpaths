#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

# Download oneDPL source if it doesn't already exist
if [ ! -f "oneDPL-2022.6.0-rc1.tar.gz" ]; then
  curl -O -L -s https://github.com/oneapi-src/oneDPL/archive/refs/tags/oneDPL-2022.6.0-rc1.tar.gz
fi

# Extract the tar file only if the directory doesn't exist
if [ ! -d "oneDPL-oneDPL-2022.6.0-rc1" ]; then
  tar xvzf oneDPL-2022.6.0-rc1.tar.gz
fi

# Clean up the tar file
rm -f oneDPL-2022.6.0-rc1.tar.gz

# Install dependencies if not already installed
if ! brew list python@3.10 &>/dev/null; then
  brew install python@3.10
fi

if ! brew list libomp &>/dev/null; then
  brew install libomp
fi

if ! brew list onedpl &>/dev/null; then
  brew install onedpl
fi

if ! brew list cmake &>/dev/null; then
  brew install cmake
fi

# Uncomment if you want to use pypy:
# brew install pypy@3.10
# pypy3.10 -m venv pypy-venv
# pypy-venv/bin/pip3 install -r requirements.txt

# Run the common setup script
./setup-common.sh

# SAVE in case we need to switch to GCC:
#                   -DCMAKE_C_COMPILER=/opt/homebrew/bin/gcc-14 \
#                   -DCMAKE_CXX_COMPILER=/opt/homebrew/bin/g++-14 \
