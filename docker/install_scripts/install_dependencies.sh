#!/bin/bash
apt-get update && apt-get install -y \
    locales \
    sudo \
    build-essential \
    cmake\
    nano \
    net-tools 

./install_python.sh
./install_py_libs.sh