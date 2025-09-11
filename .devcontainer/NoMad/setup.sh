#!/bin/bash

source /opt/ros/noetic/setup.bash
source /workspace/ros1_ws/install/setup.bash
export PYTHONPATH=/workspace/.packages_nomad:$PYTHONPATH
exec "$@"
    