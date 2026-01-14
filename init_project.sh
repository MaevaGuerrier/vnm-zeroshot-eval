#!/bin/bash
target_dir=/workspace/.packages_nomad_ros2

# install diffusion_policy
pip install third_party/diffusion_policy/ --target=$target_dir
pip install src/visualnav-transformer/train --target=$target_dir
pip install src/visualnav-transformer/deployment --target=$target_dir

cd /workspace