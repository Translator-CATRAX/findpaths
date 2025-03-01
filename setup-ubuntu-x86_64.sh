#!/usr/bin/env bash

set -o nounset -o pipefail -o errexit

# Check if packages are installed, if not, install them
sudo apt-get update

PACKAGES=(
    "libomp-dev"
    "cmake"
    "g++"
    "python3.10-venv"
    "python3.10-dev"
    "libtbb-dev"
)

for package in "${PACKAGES[@]}"; do
    if ! dpkg -s "$package" >/dev/null 2>&1; then
        sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "$package"
    fi
done

# Check if the Intel GPG key is already added
if ! gpg --list-keys | grep -q "Intel Software Products"; then
    wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
        | gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null
fi

# Check if the repository is already added
if ! grep -q "^deb .*/oneapi" /etc/apt/sources.list.d/oneAPI.list 2>/dev/null; then
    echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" \
        | sudo tee /etc/apt/sources.list.d/oneAPI.list
    sudo apt-get update
fi

# Install Intel BaseKit if not installed
if ! dpkg -s "intel-basekit" >/dev/null 2>&1; then
    sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y intel-basekit
fi

# Run the setup script if it exists and is executable
if [[ -x "./setup-common.sh" ]]; then
    ./setup-common.sh
else
    echo "setup-common.sh not found or not executable"
    exit 1
fi


