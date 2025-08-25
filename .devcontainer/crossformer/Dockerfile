# Base image
FROM nvcr.io/nvidia/l4t-base:r36.2.0

# Non-interactive
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/conda/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libssl-dev libusb-1.0-0-dev pkg-config \
    libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
    libasio-dev curl udev apt-transport-https ca-certificates swig \
    wget software-properties-common python3-pip nano \
    && rm -rf /var/lib/apt/lists/*

# Add ROS 2 repo key and source
RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        | gpg --dearmor > /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Install ROS 2 Humble base packages
RUN apt-get update && apt-get install -y \
    ros-humble-ros-base \
    ros-humble-ament-cmake \
    python3-colcon-common-extensions \
    python3-argcomplete \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O /tmp/miniconda.sh
RUN bash /tmp/miniconda.sh -b -p /opt/conda
RUN rm /tmp/miniconda.sh
ENV PATH="/opt/conda/bin:${PATH}"

RUN /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
RUN /opt/conda/bin/conda config --remove channels defaults || true && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda config --set channel_priority strict
# Create Conda environment


COPY crossformer_environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# copy the activation command to bashrc
RUN echo "source /opt/conda/etc/profile.d/conda.sh && conda activate crossformer_env" >> ~/.bashrc



# Copy requirements.txt for pip
# Download the NVIDIA TensorFlow wheel
RUN wget https://developer.download.nvidia.com/compute/redist/jp/v60/tensorflow/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl -O /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
RUN /opt/conda/bin/conda run -n crossformer_env pip install --upgrade pip setuptools wheel
RUN /opt/conda/bin/conda run -n crossformer_env pip install -v /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
COPY requirements.txt /tmp/requirements.txt
RUN /opt/conda/bin/conda run -n crossformer_env pip install --no-deps flax==0.7.5
RUN /opt/conda/bin/conda run -n crossformer_env pip install -v -r /tmp/requirements.txt

# RUN git clone https://github.com/rail-berkeley/crossformer.git
# RUN cd crossformer &&\
#     /opt/conda/bin/conda run -n crossformer_env pip install -e .

# Copy setup script
ARG CACHE_BUST=2
COPY ./setup.sh /tmp/setup.sh
RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc

# Default entrypoint
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash", "-c", "source ~/.bashrc && exec bash"]
# CMD ["bash","-l"]
