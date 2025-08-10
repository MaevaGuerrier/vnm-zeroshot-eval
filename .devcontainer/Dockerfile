# FROM img_name:tag
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

RUN apt-get update \
    && apt-get install -qq -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \    
    curl \	
    libusb-1.0-0 \
    udev \
    apt-transport-https \
    ca-certificates \
    curl \
    swig \
    wget \
    software-properties-common \
    python3-pip \
    nano

RUN apt-get update && sh -c 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros-latest.list' && \
    wget http://packages.ros.org/ros.key -O - | apt-key add - 
  

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-ros-base \
    tmux ros-noetic-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*


RUN pip install numpy matplotlib==3.5.1 pyyaml wandb \
        einops \
        vit-pytorch \
  		rospkg      \
  		defusedxml  \
  		huggingface_hub==0.23.5 \
		efficientnet_pytorch \
		warmup_scheduler \
		diffusers==0.11.1 \
                prettytable

RUN git clone https://github.com/real-stanford/diffusion_policy.git &&\
    pip install -e diffusion_policy/

COPY ./setup.sh /tmp/setup.sh
