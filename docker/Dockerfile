FROM nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04

# proxy needs to be provided from the outside
ARG DOCKER_PROXY=""

# run build using bash
SHELL ["/bin/bash", "-c"]

# set proxy
ENV http_proxy="${DOCKER_PROXY}"
ENV https_proxy="${DOCKER_PROXY}"
ENV ftp_proxy="${DOCKER_PROXY}"
ENV HTTP_PROXY="${DOCKER_PROXY}"
ENV HTTPS_PROXY="${DOCKER_PROXY}"
ENV FTP_PROXY="${DOCKER_PROXY}"

# set the device order to match nvidia-smi
ENV CUDA_DEVICE_ORDER="PCI_BUS_ID"

# avoid user interaction when installing tzdata
ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN set -ex && \
    # install debian packages
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    subversion \
    cmake \
    autoconf \
    automake \
    libtool \
    yasm \
    nasm \
    tcl \
    libx11-dev \
    libxxf86vm-dev \
    libxcursor-dev \
    libxi-dev \
    libxrandr-dev \
    libxinerama-dev \
    libglew-dev \
    # make deps
    # - openal
    libasound2-dev \
    pulseaudio \
    libpulse-dev \
    # - osl
    flex \
    bison \
    libbison-dev \
    libpugixml-dev \
    python \
    # - ?
    libexpat1-dev \
    # dev
    vim \
    && \
    apt-get clean

RUN mkdir ~/blender-git && cd ~/blender-git && git clone --branch v2.81a http://git.blender.org/blender.git && cd ~/blender-git/blender && git submodule init && git submodule update

RUN cd ~/blender-git/blender && make deps

RUN mkdir ~/blender-git/build && cd ~/blender-git/build

RUN echo "cmake -D WITH_PYTHON_INSTALL=OFF -D WITH_AUDASPACE=OFF -D WITH_PYTHON_MODULE=ON -D WITH_CYCLES_CUDA_BINARIES=ON -D WITH_INSTALL_PORTABLE=ON ../blender" >> ~/blender-git/build/run_configure.sh && chmod +x ~/blender-git/build/run_configure.sh

# unset proxy
#ENV http_proxy=""
#ENV https_proxy=""
#ENV ftp_proxy=""
#ENV HTTP_PROXY=""
#ENV HTTPS_PROXY=""
#ENV FTP_PROXY=""
#ENV no_proxy=""

