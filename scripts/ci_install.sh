#!/bin/sh

set -e

# This is all far from perfect as it requires manual updates of the version, but it's a start

CACHE_DIR="${HOME}/.blender_download_cache"
DOWNLOAD_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.83/blender-2.83.0-linux64.tar.xz"
DL_TARGET_FILE="${CACHE_DIR}/blender.tar.xz"
BLENDER_DIR="${HOME}/blender"

echo "Installing Blender. Checking cache..."
if [ ! -f $DL_TARGET_FILE ]; then
    echo "Blender archive not found in cache, downloading..."
    mkdir -p $CACHE_DIR
    wget -O $DL_TARGET_FILE $DOWNLOAD_URL
fi

mkdir -p $BLENDER_DIR
tar xvf $DL_TARGET_FILE -C $BLENDER_DIR --strip 1
echo "Extracted archive to ${HOME}. Installing pip, blender_kitti"
${HOME}/blender/2.83/python/bin/python3.7m ${HOME}/blender/2.83/python/lib/python3.7/ensurepip
${HOME}/blender/2.83/python/bin/pip3 install -e .
