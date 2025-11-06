# Declare build args (Docker passes these automatically with buildx)
ARG TARGETARCH
ARG TARGETOS


# =========================
# Base for amd64 (PC/server)
# =========================
FROM tensorflow/tensorflow:2.15.0-gpu AS base-amd64

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    wget curl git lsb-release gnupg2 build-essential \
    python3.10 python3.10-dev python3.10-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
&& update-alternatives --set python /usr/bin/python3.10


# Install TensorFlow GPU (PyPI provides wheels for amd64)
RUN pip install -V tensorflow==2.15.0 
COPY requirements_pc.txt /tmp/requirements.txt
RUN pip install -v -r /tmp/requirements.txt

# Final image selection
# =========================
FROM base-${TARGETARCH}
ARG CACHE_BUST=3
COPY ./setup.sh /tmp/setup.sh
RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc

# Default entrypoint
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash", "-c", "source ~/.bashrc && exec bash"]