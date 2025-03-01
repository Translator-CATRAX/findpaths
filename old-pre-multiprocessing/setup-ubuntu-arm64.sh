#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

sudo apt-get update

sudo apt-get install -y \
     libomp-dev \
     cmake \
     g++ \
     clang \
     python3.10-venv \
     python3.10-dev \
     llvm \
     libtbb-dev

curl -O -L -s https://github.com/oneapi-src/oneDPL/archive/refs/tags/oneDPL-2022.6.0-rc1.tar.gz
tar xvzf oneDPL-2022.6.0-rc1.tar.gz
rm -f oneDPL-2022.6.0-rc1.tar.gz

onedpl_root=/usr/local/onedpl
sudo rm -r -f ${onedpl_root}
onedpl_cmake=${onedpl_root}/lib/cmake/oneDPL
onedpl_linux=${onedpl_root}/linux
sudo mkdir -p ${onedpl_cmake}
sudo mkdir -p ${onedpl_linux}

cd oneDPL-oneDPL-2022.6.0-rc1
cmake -DSKIP_HEADERS_SUBDIR=FALSE -P cmake/scripts/generate_config.cmake
sudo cp output/oneDPLConfig.cmake ${onedpl_cmake}
sudo cp output/oneDPLConfigVersion.cmake ${onedpl_cmake}
sudo cp -r include/ ${onedpl_linux}
cd ..

if [ -f ./setup-common.sh ]; then
    ./setup-common.sh
fi

