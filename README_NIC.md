# Installation and setup
1. `git clone https://github.com/MaevaGuerrier/visualnav-transformer.git` or `git clone git@github.com:MaevaGuerrier/visualnav-transformer.git ` to clone the repository.
2. Inside the directory SafeGMN, select the branch corresponding to the navigation method : `git checkout [branch]`.
3. Run `git submodule update --init` and `git submodule foreach git pull origin main`.

4. Inside Dockerfile, adjust the RUN PIP instruction so there is no incompatibility. Example :
`RUN pip install \
    "fsspec<2024.0.0" \
    "aiohttp<3.9.0" \
    "async-timeout<5.0" \
    "pydantic<2" \
    "wandb<0.16" \
    typing-extensions==4.7.1 \
    "filelock<3.13" \
    matplotlib==3.5.1 \
    torch==2.4.0 torchvision --extra-index-url https://download.pytorch.org/whl/cu124 \
    pyyaml \
    einops \
    vit-pytorch \
    rospkg \
    defusedxml \
    efficientnet_pytorch \
    huggingface_hub==0.23.5 \
    warmup_scheduler \
    diffusers==0.11.1 \
    numpy==1.24.4 \
    sympy==1.11.1 \
    scipy==1.10.1 \
    bagpy \
    networkx==3.1 \
    prettytable`

5. Then, use the command `./docker_setup.py` to build image. If any incompatibility, it is possible that you need to adjust the Dockerfile by downgrading or upgrading some package.
6. Again, use `./docker_setup.py` to start a container and run `./init_project.sh`. If the file isn't there, you can create one that look like this (don't forget to `chmod +x init_project.sh` to make it executable):
```
#!/bin/bash
target_dir=/workspace/.packages_nomad

# install diffusion_policy
pip install third_party/diffusion_policy/ --target=$target_dir
pip install src/visualnav-transformer/train --target=$target_dir

# install visualnav_transformer
# pip install src/visualnav-transformer/train/ --target=$target_dir
# pip install crossformer/ --target=$target_dir
# pip install robo-gym/ --target=$target_dir 
# pip install "scipy==1.12"

# build sim_ws
#cd sim_ws/
#catkin build 
#source devel/setup.bash

cd /workspace
```
7. Inside `/src/visualnav-transformer/deployment/src` of the workspace directory, add a new directory `model_weights` containing the weights of the model to use (.PTH for now).
8. Inside `/src/visualnav-transformer/deployment/src/topomaps/images` of the workspace directory, add a new directory containing the topomap images.
9. Be certain that `robot.yaml` that the paths of the topics are correct depending on robot/node. Also, you can verify the `topic_names.py` so that `IMAGE_TOPIC` is set correctly. Example : `vel_navi_topic: /cmd_vel` in `robot.yaml` and `IMAGE_TOPIC = "/camera/image_raw"` in `topic_names.py`.

# Run the simulation
From workspace `cd src/visualnav-transformer/deployment/src`.
Then run `./navigate.sh "--dir [topomap_dir]"`.
