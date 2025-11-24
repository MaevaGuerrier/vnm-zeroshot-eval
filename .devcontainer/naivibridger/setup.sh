#!/bin/bash
# source ~/.bashrc
# source 
target="/workspace/.packages_naivibridger"
source /opt/ros/noetic/setup.bash
export PYTHONPATH=${target}:$PYTHONPATH
exec "$@"
