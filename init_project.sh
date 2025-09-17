#!/bin/bash

target=/workspace/.packages_safegnm

pip3 install third_party/self_supervised_segmentation/ --target $target

pip3 install /workspace/third_party/wild_visual_navigation/ --target $target

pip3 install /workspace/third_party/diffusion_policy/ --target $target

# check if stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt exists in /workspace/third_party/self_supervised_segmentation/models
if [ ! -f /workspace/third_party/self_supervised_segmentation/models/stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt ]; then
    ./workspace/third_party/self_supervised_segmentation/download_model.sh
fi


mkdir /workspace/.packages_safegnm/models/  
cp /workspace/third_party/self_supervised_segmentation/models/stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt /workspace/.packages_safegnm/models/


# TODO 
# IF WE KEEP TARGET WE HAVE TO CP HERE --> /workspace/.packages_safegnm/.tmp_state_dict.pt
# cp /workspace/third_party/wild_visual_navigation/assets/checkpoints/indoor_mpi.pt /workspace/.packages_safegnm/.tmp_state_dict.pt

# cp /workspace/third_party/wild_visual_navigation/assets/checkpoints/mountain_bike_trail_v2.pt /workspace/.packages_safegnm/.tmp_state_dict.pt

pip3 install /workspace/src/visualnav-transformer/train/ --target $target

pip3 install rosnumpy --target $target

pip3 install --upgrade attrs --target $target

pip3 install --upgrade --force-reinstall numpy --target $target

pip3 install efficientnet-pytorch --target $target

pip3 install einops --target $target

pip3 install vit-pytorch --target $target

pip3 install diffusers --target $target