#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

# Remove the build directory if it exists, then create it
rm -r -f build
mkdir -p build

# Change to the build directory
CWD=$(pwd)
cd build

# Run cmake with specified options
cmake .. \
      -DCMAKE_PREFIX_PATH="${CWD}/oneDPL-oneDPL-2022.6.0-rc1;/opt/homebrew/opt:/opt/homebrew/opt/tbb" \
      -DCMAKE_CXX_FLAGS="-O3 -I${CWD}/oneDPL-oneDPL-2022.6.0-rc1/include -I${CWD}/oneDPL-oneDPL-2022.6.0-rc1/include/oneapi"

# Build the project
make VERBOSE=1

# Return to the original directory
cd ..

# Copy the built file to the current directory
cp build/findpaths_core.cpython-310-darwin.so .
