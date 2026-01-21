# FROM img_name:tag
FROM dustynv/l4t-pytorch:r36.2.0
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

# RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
#     && curl -sSL 'https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc' | apt-key add -

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ros-noetic-ros-base \
#     tmux \
#     python3-catkin-tools \
#     ros-noetic-cv-bridge \
#     python3-rosdep \
#     ros-noetic-teleop-twist-keyboard \
#     && rm -rf /var/lib/apt/lists/*

# Add ROS 2 repo key and source
RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        | gpg --dearmor > /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Install ROS 2 Humble base packages
RUN apt update && apt install -y \
    ros-humble-ros-base \
    ros-humble-ament-cmake \
    ros-humble-rmw-zenoh-cpp \
    ros-humble-cv-bridge \
    ros-humble-nav-msgs \
    python3-colcon-common-extensions \
    python3-argcomplete \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir --index-url https://pypi.org/simple \
    matplotlib==3.5.1 \
    pyyaml \
    einops \
    vit-pytorch==1.12.4 \
    rospkg \
    defusedxml \
    protobuf==3.20 \
    huggingface_hub==0.23.5 \
    efficientnet_pytorch \
    warmup_scheduler \
    diffusers==0.11.1 \
    numpy==1.24.4 \
    scipy==1.10.1 \
    prettytable \
    onnx \
    pycuda \
    bagpy \
    coloredlogs \
    flatbuffers \
    wandb \
    sympy 


RUN wget https://nvidia.box.com/shared/static/6l0u97rj80ifwkk8rqbzj1try89fk26z.whl -O onnxruntime_gpu-1.19.0-cp310-cp310-linux_aarch64.whl && \
    pip install --no-deps onnxruntime_gpu-1.19.0-cp310-cp310-linux_aarch64.whl && \
    rm onnxruntime_gpu-1.19.0-cp310-cp310-linux_aarch64.whl 

ARG CACHE_BUST=2
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]