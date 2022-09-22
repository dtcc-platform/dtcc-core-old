#!/bin/bash

python3 -m pip install \
	redis \
	pika \
	numpy \
	fastapi \
	uvicorn[standard] \
	laspy[lazrs] \
	protobuf==3.20.* \
	h5py \
	python-dotenv \
	argparse \
	tqdm \
	rocketry \
	sse-starlette \
	aio-pika \
	pika

# These libraries require all of gdal-dev to be apt installed if you want to install them via pip
# so we install them like this for now
apt-get update && apt-get install -y python3-fiona python3-rasterio
