#!/usr/bin/env bash

PYTHON_DIR=./dtcc
echo "Building Python classes..."
protoc --python_out=$PYTHON_DIR --proto_path=../dtcc-model/protobuf dtcc.proto