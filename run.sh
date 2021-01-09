#!/bin/bash

xhost +local:meter
docker pull andrey540/meter
docker run -it --net=host --ipc=host -e DISPLAY=$DISPLAY -v "$HOME"/projects/meter/app:/usr/local/app --device /dev/video0:/dev/video0 andrey540/meter
