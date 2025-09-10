# FROM img_name:tag
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3
ENV DEBIAN_FRONTEND=noninteractive

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
    apt-utils \
    python3-grpcio \
    python3-scipy \
    psmisc \
    vim-gtk \ 
    libcppunit-dev \
    python3-pip \
    nano

RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
    && curl -sSL 'https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc' | apt-key add -

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ros-noetic-ros-base ros-noetic-vision-opencv ros-noetic-cv-bridge \
#     tmux ros-noetic-teleop-twist-keyboard ros-noetic-usb-cam\
#     && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-ros-base \
    tmux ros-noetic-teleop-twist-keyboard\
    && rm -rf /var/lib/apt/lists/*

RUN pip install matplotlib==3.5.1 \
                robo-gym-server-modules \ 
                pyyaml wandb \
                einops \
                vit-pytorch \
  		        rospkg \
  		        defusedxml \
                protobuf==3.20 \
  		        huggingface_hub==0.23.5 \
		        efficientnet_pytorch \
		        warmup_scheduler \
		        diffusers==0.11.1 \
                prettytable \
                cv-bridge


# diffusion policy for NoMad 
RUN git clone https://github.com/real-stanford/diffusion_policy.git &&\
    pip install -e diffusion_policy/

# DUMMY VAR TO MAKE CHANGES ONLY HERE CHANGE THE NUMBER
ARG R=2
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]
