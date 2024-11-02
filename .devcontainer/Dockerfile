# FROM img_name:tag
FROM limo_ros1:dev 

ENV DEBIAN_FRONTEND=noninteractive

# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda 
ENV PATH=$CONDA_DIR/bin:$PATH

COPY ./deployment_environment.yaml /tmp/deployment_environment.yaml  
# RUN wget https://github.com/MaevaGuerrier/visualnav-transformer/blob/main/deployment/deployment_environment.yaml && \
RUN conda env create -f /tmp/deployment_environment.yaml

RUN conda init && \
    echo "conda activate vint_deployment" >> ~/.bashrc
    # pip install -e train/

# RUN echo "source /opt/ros/noetic/setup.bash " >> ~/.bashrc && \
#     echo "source /workspace/catkin_ws/devel/setup.bash " >> ~/.bashrc

# ENTRYPOINT ["/tmp/setup.sh"] 

# RUN git clone https://github.com/YDLIDAR/YDLidar-SDK.git &&\
#     mkdir -p YDLidar-SDK/build && \
#     cd YDLidar-SDK/build &&\
#     cmake ..&&\
#     make &&\
#     make install &&\
#     cd .. &&\
#     pip install . &&\
#     cd .. && rm -r YDLidar-SDK 

