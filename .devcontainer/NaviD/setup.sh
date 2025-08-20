#!/bin/bash

source /opt/ros/noetic/setup.bash
export PYTHONPATH=/workspace/.packages_navid:$PYTHONPATH

# TARGET_DIR="/workspace/ViNT_NaviD"

# # ===== Enter directory =====
# cd "$TARGET_DIR" || {
#     echo "⚠ Failed to enter directory $TARGET_DIR. Continuing..."
# }   

# pip install -e train/

# pip install -e diffusion_policy/

# pip install -r Depth-Anything-V2/requirements.txt 

# pip install -e Depth-Anything-V2/.

# # ===== Install Python dependencies (ignore failures) =====
# echo "Installing Python packages opencv<4.3, numpy 1.19.4, open3d"
# pip install "opencv-python-headless<4.3"
# pip install "numpy==1.19.4"
# pip install open3d

exec "$@"