#!/bin/bash

python3 -m pip install \
	redis \
	pika \
	numpy \
	fastapi \
	uvicorn[standard] \
	protobuf==3.20.*
