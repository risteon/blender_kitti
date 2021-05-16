FROM nvidia/cuda:11.3.0-cudnn8-devel-ubuntu20.04

# proxy needs to be provided from the outside
ARG DOCKER_PROXY_HOST=""
ARG DOCKER_PROXY_PORT=""

# run build using bash
SHELL ["/bin/bash", "-c"]

# set proxy
ENV http_proxy="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"
ENV https_proxy="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"
ENV ftp_proxy="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"
ENV HTTP_PROXY="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"
ENV HTTPS_PROXY="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"
ENV FTP_PROXY="http://${DOCKER_PROXY_HOST}:${DOCKER_PROXY_PORT}"

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
    libx11-dev \
    libxxf86vm-dev \
    libxcursor-dev \
    libxi-dev \
    libxrandr-dev \
    libxinerama-dev \
    libglew-dev \
    python3 \
    && \
    apt-get clean

RUN mkdir /blender-git && cd /blender-git && git clone --branch blender-v2.92-release https://git.blender.org/blender.git && cd /blender-git/blender && git submodule update --init --recursive

# tmp: if clone through proxy failed
# COPY blender-git /blender-git/

# let subversion create config dir
RUN svn checkout > /dev/null 2>&1; exit 0
# fill in proxy conf
RUN printf "[global]\nhttp-proxy-host = ${DOCKER_PROXY_HOST}\nhttp-proxy-port = ${DOCKER_PROXY_PORT}\n" >> ~/.subversion/servers

# precompiled library deps
RUN mkdir /blender-git/lib && cd /blender-git/lib && svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/linux_centos7_x86_64

WORKDIR /blender-git/blender
CMD ["make", "bpy"]

# unset proxy
ENV http_proxy=""
ENV https_proxy=""
ENV ftp_proxy=""
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV FTP_PROXY=""
ENV no_proxy=""

