# FROM img_name:tag
FROM dustynv/l4t-pytorch:2.2-r35.4.1
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

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-ros-base \
    tmux \
    python3-catkin-tools \
    ros-noetic-cv-bridge \
    python3-rosdep \
    ros-noetic-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --index-url https://pypi.org/simple matplotlib==3.5.1 \
                robo-gym-server-modules \ 
                pyyaml \
                einops \
                vit-pytorch \
  		        rospkg \
  		        defusedxml \
                protobuf==3.20 \
  		        huggingface_hub==0.23.5 \
		        efficientnet_pytorch \
		        warmup_scheduler \
		        diffusers==0.11.1 \
                numpy==1.24.4 \
                prettytable

# diffusion policy for NoMad 
# RUN git clone https://github.com/real-stanford/diffusion_policy.git &&\
#     pip install -e diffusion_policy/

# DUMMY VAR TO MAKE CHANGES ONLY HERE CHANGE THE NUMBER
ARG CACHE_BUST=1
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]
