#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

# Remove the build directory if it exists, then recreate it
rm -r -f build
mkdir -p build
cd build

# Define the OneDPL root and include paths
onedpl_root=/usr/local/onedpl
onedpl_include=${onedpl_root}/linux/include

# Run CMake with the specified configuration
cmake .. \
      -DoneDPL_DIR="${onedpl_root}" \
      -DCMAKE_CXX_COMPILER="/usr/bin/clang++" \
      -DCMAKE_PREFIX_PATH="${onedpl_root}/lib/cmake/oneDPL" \
      -DCMAKE_CXX_FLAGS="-O3 -I${onedpl_include}/oneapi -I${onedpl_include}"

# Build the project with verbose output
make VERBOSE=1

# Return to the original directory
cd ..

# Copy the generated file to the current directory (adjust if the name differs)
cp build/findpaths_core.cpython-310-aarch64-linux-gnu.so .

