#!/bin/bash

source /opt/ros/noetic/setup.bash
export PYTHONPATH=/workspace/.packages_care:$PYTHONPATH
exec "$@"
