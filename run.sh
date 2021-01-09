#!/bin/bash

#exec xhost +local:meter
exec docker run -it --net=host --ipc=host -e DISPLAY=$DISPLAY -v "$HOME"/projects/meter/app:/usr/local/app --device /dev/video0:/dev/video0 meter
