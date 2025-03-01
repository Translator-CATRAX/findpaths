#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

# Remove the build directory only if it exists
if [[ -d "build" ]]; then
    rm -rf build
fi

# Create the build directory if it doesn't exist
mkdir -p build
cd build

# Check if CMake has been configured and regenerate it only if needed
if [[ ! -f "CMakeCache.txt" ]]; then
    cmake .. \
        -DoneDPL_DIR=/opt/intel/oneapi/2024.2/lib/cmake/oneDPL \
        -DCMAKE_PREFIX_PATH=/opt/intel/oneapi/2024.2 \
        -DCMAKE_CXX_FLAGS="-O3 -I/opt/intel/oneapi/2024.2/include/oneapi"
fi

# Run the make command only if needed (e.g., recompile if source files have changed)
if [[ ! -f "findpaths_core.cpython-310-x86_64-linux-gnu.so" ]]; then
    make VERBOSE=1
fi

cd ..

# Copy the built file only if it has been newly compiled or updated
if [[ -f "build/findpaths_core.cpython-310-x86_64-linux-gnu.so" ]]; then
    cp build/findpaths_core.cpython-310-x86_64-linux-gnu.so .
else
    echo "Error: Compiled file not found"
    exit 1
fi

