#!/usr/bin/env bash

docker stop sim-gst 
docker rm sim-gst 

docker run --rm --runtime=nvidia -ti \
    -v $(pwd):/home/sim/ \
    -p 8554:8554 \
    -p 9000:9000 \
    --name sim-gst \
    sim-gst
