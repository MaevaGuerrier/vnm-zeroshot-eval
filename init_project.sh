#!/bin/bash

target=/workspace/.packages_naivibridger

pip3 install /workspace/third_party/diffusion_policy/ --target $target


pip3 install /workspace/src/NaiviBridger/train/ --target $target

# pip3 install rosnumpy --target $target

# pip3 install --upgrade attrs --target $target

# pip3 install --upgrade --force-reinstall numpy --target $target

# pip3 install efficientnet-pytorch --target $target

# pip3 install einops --target $target

# pip3 install vit-pytorch --target $target

# pip3 install diffusers==0.11.1 --target $target