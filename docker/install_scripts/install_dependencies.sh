#!/bin/bash

apt-get update && apt-get install -y \
    build-essential \
    cmake\
    nano \
    net-tools \
    protobuf-compiler

./install_python.sh
./install_py_libs.sh
