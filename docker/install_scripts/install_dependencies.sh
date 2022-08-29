#!/bin/bash

apt-get update && apt-get install -y \
    build-essential \
    cmake \
    nano \
    net-tools \
    wget \
    unzip \
    protobuf-compiler \
    libprotobuf-dev \
    pybind11-dev



#./install_protobuf.sh
./install_python.sh
./install_py_libs.sh
./install_assimp.sh
