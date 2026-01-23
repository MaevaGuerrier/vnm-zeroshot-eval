#!/bin/bash

# CAREFUL MAKE SURE TARGET DIR IS CORRECT
target_dir="/workspace/.packages_naivibridger_ros2"

# We had issues when changing package contents, remaining build files would interfere when installing again.
# Clean everything
echo "Cleaning all build artifacts"
rm -rf "$target_dir" # CAREFUL MAKE SURE TARGET DIR IS CORRECT
find /workspace/src/NaiviBridger/ -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null


echo "Installing packages to $target_dir"
pip install /workspace/third_party/diffusion_policy/ --target="$target_dir"
pip install /workspace/src/NaiviBridger/deployment/ --target="$target_dir"
pip install /workspace/src/NaiviBridger/train/ --target="$target_dir"