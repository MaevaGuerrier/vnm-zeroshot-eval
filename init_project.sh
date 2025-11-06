#!/bin/bash
target_dir=/workspace/.packages_crossformer

# install diffusion_policy
#pip install diffusion_policy/ --target=$target_dir

# install visualnav_transformer
pip install src/visualnav-transformer/train/ --target=$target_dir
pip install crossformer/ --target=$target_dir
pip install robo-gym/ --target=$target_dir 
pip install "scipy==1.12"

# build sim_ws
#cd sim_ws/
#catkin build 
#source devel/setup.bash

cd /workspace