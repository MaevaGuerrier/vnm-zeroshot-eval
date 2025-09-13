#!/bin/bash
# source ~/.bashrc
# source 

source /opt/ros/noetic/setup.bash
export PYTHONPATH=/workspace/.packages_safegnm:$PYTHONPATH
exec "$@"
