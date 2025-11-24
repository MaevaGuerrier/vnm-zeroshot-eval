#!/bin/bash

target=/workspace/.packages_naivibridger

pip3 install /workspace/third_party/diffusion_policy/ --target $target


pip3 install /workspace/src/NaiviBridger/train/ --target $target

