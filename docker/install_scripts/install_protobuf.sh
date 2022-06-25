#!/bin/bash

if [[ $(uname -m) == aarch64 ]]
then
    wget https://github.com/protocolbuffers/protobuf/releases/download/v21.1/protoc-21.1-linux-aarch_64.zip
    mkdir protoc-21.1
    mv protoc-21.1-linux-aarch_64.zip protoc-21.1
    cd protoc-21.1
    unzip protoc-21.1-linux-aarch_64.zip
else
    wget https://github.com/protocolbuffers/protobuf/releases/download/v21.1/protoc-21.1-linux-x86_64.zip
    mkdir protoc-21.1
    mv protoc-21.1-linux-x86_64.zip protoc-21.1
    cd protoc-21.1
    unzip protoc-21.1-linux-x86_64.zip
fi

cp bin/protoc /usr/local/bin
cp -r include/google /usr/local/include
