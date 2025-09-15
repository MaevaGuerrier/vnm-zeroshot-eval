#!/bin/bash
pip3 install /workspace/third_party/self_supervised_segmentation/

pip3 install /workspace/third_party/wild_visual_navigation/

# check if stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt exists in /workspace/third_party/self_supervised_segmentation/models
if [ ! -f /workspace/third_party/self_supervised_segmentation/models/stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt ]; then
    ./workspace/third_party/self_supervised_segmentation/download_model.sh
fi

# check if /usr/local/lib/python3.8/dist-packages/models/ exists, if not create it
if [ ! -d /usr/local/lib/python3.8/dist-packages/models/ ]; then
    mkdir /usr/local/lib/python3.8/dist-packages/models/
fi

cp /workspace/third_party/self_supervised_segmentation/models/stego_cocostuff27_vit_base_5_cluster_linear_fine_tuning.ckpt /usr/local/lib/python3.8/dist-packages/models/

cp /workspace/third_party/wild_visual_navigation/assets/checkpoints/indoor_mpi.pt /usr/local/lib/python3.8/dist-packages/.tmp_state_dict.pt

pip3 install /workspace/src/visualnav-transformer/train/

pip3 install rosnumpy

pip3 install --upgrade attrs
   
pip3 install --upgrade --force-reinstall numpy
